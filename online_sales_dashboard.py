import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv(r"D:\Data since\Epsilon AI\DSP\Mid_project_1\Online Sales Dataset\online_sales_dataset_cleaned.csv")  # Replace with your actual file

df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")
country = st.sidebar.multiselect("Country", df["country"].unique())
category = st.sidebar.multiselect("Category", df["category"].unique())
year = st.sidebar.multiselect("Order Year", sorted(df["order_year"].unique()))
return_status = st.sidebar.multiselect("Return Status", df["return_status"].unique())

filtered_df = df.copy()
if country:
    filtered_df = filtered_df[filtered_df["country"].isin(country)]
if category:
    filtered_df = filtered_df[filtered_df["category"].isin(category)]
if year:
    filtered_df = filtered_df[filtered_df["order_year"].isin(year)]
if return_status:
    filtered_df = filtered_df[filtered_df["return_status"].isin(return_status)]

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Data Table", "Customer Segmentation", "Product Insights", "Trends"
])

# TAB 1: Overview
with tab1:
    st.header("📊 Sales Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"${filtered_df['sales'].sum():,.2f}")
    col2.metric("Total Orders", f"{filtered_df['invoice_num'].nunique():,}")
    col3.metric("Avg. Order Value", f"${filtered_df['sales'].mean():.2f}")

    st.subheader("Sales by Month")
    month_sales = filtered_df.groupby("order_month")["sales"].sum().reset_index()
    st.plotly_chart(px.bar(month_sales, x="order_month", y="sales", labels={"sales": "Sales ($)"}), use_container_width=True)

# TAB 2: Data Table
with tab2:
    st.header("📁 Filtered Data Table")
    st.dataframe(filtered_df)
    st.download_button("Download CSV", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv", mime="text/csv")

# TAB 3: RFM Segmentation
with tab3:
    st.header("🧠 RFM Customer Segmentation")

    # Combine date parts into a datetime
    df["order_date"] = pd.to_datetime(
        df["order_year"].astype(str) + "-" +
        df["order_month"].astype(str) + "-1"
    )

    max_date = df["order_date"].max()

    # RFM Calculation
    rfm = df.groupby("customer_id").agg({
        "order_date": lambda x: (max_date - x.max()).days,
        "invoice_num": "nunique",
        "sales": "sum"
    }).rename(columns={
        "order_date": "Recency",
        "invoice_num": "Frequency",
        "sales": "Monetary"
    }).reset_index()

    # Score each RFM metric from 1 to 4
    rfm["R_Score"] = pd.qcut(rfm["Recency"], q=4, labels=[4, 3, 2, 1])
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), q=4, labels=[1, 2, 3, 4])
    rfm["M_Score"] = pd.qcut(rfm["Monetary"], q=4, labels=[1, 2, 3, 4])

    # Combine into single score
    rfm["RFM_Segment"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)
    rfm["RFM_Score"] = rfm[["R_Score", "F_Score", "M_Score"]].astype(int).sum(axis=1)

    # Segment labeling (simplified)
    def segment_map(score):
        if score >= 9:
            return "Champions"
        elif score >= 7:
            return "Loyal"
        elif score >= 5:
            return "Potential"
        else:
            return "At Risk"

    rfm["Segment"] = rfm["RFM_Score"].apply(segment_map)

    st.dataframe(rfm)

    st.subheader("📊 Segment Distribution")
    fig = px.histogram(rfm, x="Segment", color="Segment", title="Customer Segment Counts")
    st.plotly_chart(fig, use_container_width=True)

# TAB 4: Product Insights
with tab4:
    st.header("📦 Product Sales Insights")
    top_products = filtered_df.groupby("description")["sales"].sum().nlargest(10).reset_index()
    fig_products = px.bar(top_products, x="sales", y="description", orientation="h")
    st.plotly_chart(fig_products, use_container_width=True)

    st.subheader("Sales by Category")
    cat_sales = filtered_df.groupby("category")["sales"].sum().reset_index()
    st.plotly_chart(px.pie(cat_sales, values="sales", names="category", title="Sales by Category"))

# TAB 5: Trends
with tab5:
    st.header("📈 Sales Trends")

    st.subheader("Hourly Sales")
    hourly_sales = filtered_df.groupby("order_hour")["sales"].sum().reset_index()
    st.plotly_chart(px.line(hourly_sales, x="order_hour", y="sales", markers=True), use_container_width=True)

    st.subheader("Weekday Sales")
    weekday_sales = filtered_df.groupby("order_weekday")["sales"].sum().reset_index()
    st.plotly_chart(px.bar(weekday_sales, x="order_weekday", y="sales"), use_container_width=True)

    st.subheader("Refund Rate Over Time")
    refund_df = filtered_df.groupby("order_month")["is_refund"].mean().reset_index()
    st.plotly_chart(px.line(refund_df, x="order_month", y="is_refund", markers=True, title="Refund Rate by Month"), use_container_width=True)
