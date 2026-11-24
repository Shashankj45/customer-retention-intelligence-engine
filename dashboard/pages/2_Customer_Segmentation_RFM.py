"""
Page 2: Customer Segmentation & RFM Matrix.
Visualizes Recency, Frequency, and Monetary (RFM) segmentation, behavioral clusters, and segment transitions.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.database.sql_runner import SQLAnalyticsRunner

st.set_page_config(page_title="Customer Segmentation & RFM | Customer Intelligence", page_icon="🧩", layout="wide")

st.title("🧩 Customer Segmentation & RFM Matrix")
st.markdown("Quantify customer behavior, identify champion accounts, and detect dormant relationships.")
st.markdown("---")

runner = SQLAnalyticsRunner()

@st.cache_data(ttl=3600)
def load_rfm_data():
    return runner.get_rfm_data()

rfm_df = load_rfm_data()

# 1. Summary Metrics
total_cust = len(rfm_df)
champions = len(rfm_df[rfm_df["rfm_segment"] == "Champions"])
at_risk = len(rfm_df[rfm_df["rfm_segment"] == "At Risk"])
cant_lose = len(rfm_df[rfm_df["rfm_segment"] == "Can't Lose Them"])
hibernating = len(rfm_df[rfm_df["rfm_segment"] == "Hibernating"])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Customers Evaluated", f"{total_cust:,}")
c2.metric("🏆 Champions", f"{champions:,}", f"{(champions/total_cust)*100:.1f}%")
c3.metric("⚠️ At Risk", f"{at_risk:,}", f"{(at_risk/total_cust)*100:.1f}%", delta_color="inverse")
c4.metric("🚨 Can't Lose Them", f"{cant_lose:,}", f"{(cant_lose/total_cust)*100:.1f}%", delta_color="inverse")
c5.metric("💤 Hibernating", f"{hibernating:,}", f"{(hibernating/total_cust)*100:.1f}%")

st.markdown("---")

# 2. Segment Distribution Visualizations
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📊 Segment Share & Customer Volume")
    seg_counts = rfm_df["rfm_segment"].value_counts().reset_index()
    seg_counts.columns = ["rfm_segment", "count"]
    
    color_map = {
        "Champions": "#10B981",
        "Loyal Customers": "#3B82F6",
        "Potential Loyalists": "#06B6D4",
        "Recent Customers": "#8B5CF6",
        "Promising": "#EC4899",
        "At Risk": "#F59E0B",
        "Can't Lose Them": "#EF4444",
        "Hibernating": "#64748B",
        "Lost Customers": "#334155"
    }

    fig_bar = px.bar(
        seg_counts,
        x="count",
        y="rfm_segment",
        orientation="h",
        color="rfm_segment",
        color_discrete_map=color_map,
        labels={"count": "Number of Customers", "rfm_segment": "RFM Segment"}
    )
    fig_bar.update_layout(template="plotly_dark", height=420, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.subheader("🗺️ Revenue Concentration by Segment")
    seg_rev = rfm_df.groupby("rfm_segment")["monetary"].sum().reset_index()
    fig_tree = px.treemap(
        seg_rev,
        path=["rfm_segment"],
        values="monetary",
        color="rfm_segment",
        color_discrete_map=color_map,
        title="Share of Total Spend by RFM Segment"
    )
    fig_tree.update_layout(template="plotly_dark", height=420)
    st.plotly_chart(fig_tree, use_container_width=True)

st.markdown("---")

# 3. Interactive RFM 3D Scatter Explorer
st.subheader("🔍 Interactive RFM 3D Space (Recency vs Frequency vs Monetary)")
st.markdown("Explore customer clusters in 3D feature space. Rotate and zoom to inspect boundaries.")

sample_rfm = rfm_df.sample(min(1200, len(rfm_df)), random_state=42)

fig_3d = px.scatter_3d(
    sample_rfm,
    x="recency_days",
    y="frequency",
    z="monetary",
    color="rfm_segment",
    color_discrete_map=color_map,
    hover_name="customer_name",
    hover_data=["customer_id", "subscription_tier", "rfm_combined_score"],
    labels={"recency_days": "Recency (Days Inactive)", "frequency": "Frequency (Orders)", "monetary": "Monetary ($ Spend)"},
    opacity=0.75
)
fig_3d.update_layout(
    template="plotly_dark",
    height=550,
    margin=dict(l=10, r=10, t=10, b=10)
)
st.plotly_chart(fig_3d, use_container_width=True)

st.markdown("---")

# 4. Filterable Customer RFM Explorer Table
st.subheader("📋 Segment Customer Search & Export")

col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    selected_segments = st.multiselect(
        "Filter by RFM Segment:",
        options=list(rfm_df["rfm_segment"].unique()),
        default=["Champions", "At Risk", "Can't Lose Them"]
    )
with col_f2:
    search_query = st.text_input("Search Customer Name or ID:", "")

filtered_rfm = rfm_df[rfm_df["rfm_segment"].isin(selected_segments)]
if search_query:
    filtered_rfm = filtered_rfm[
        filtered_rfm["customer_name"].str.contains(search_query, case=False, na=False) |
        filtered_rfm["customer_id"].str.contains(search_query, case=False, na=False)
    ]

st.dataframe(filtered_rfm, use_container_width=True, height=350)
st.caption(f"Showing {len(filtered_rfm):,} matched customer records.")
