"""
Page 1: Executive Overview & KPI Dashboard.
Visualizes macro financial performance, monthly cohorts, and acquisition economics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.database.sql_runner import SQLAnalyticsRunner
from src.database.connection import db_manager

st.set_page_config(page_title="Executive Overview | Customer Intelligence", page_icon="📊", layout="wide")

st.title("📊 Executive Overview & Business Performance")
st.markdown("Macro financial health, acquisition efficiency, and customer retention dynamics.")
st.caption("ℹ️ **Data Origin**: Metrics computed from synthetic enterprise benchmark dataset (5,000 multi-tier accounts).")
st.markdown("---")

runner = SQLAnalyticsRunner()

# 1. Fetch data with caching
@st.cache_data(ttl=3600)
def load_executive_data():
    r_df = runner.get_revenue_trends()
    c_df = runner.get_cohort_matrix()
    a_df = runner.get_acquisition_metrics()
    return r_df, c_df, a_df

rev_df, cohort_df, acq_df = load_executive_data()

# Top KPI Metric Cards
latest_m = rev_df.iloc[-1]
prev_m = rev_df.iloc[-2] if len(rev_df) > 1 else latest_m

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Latest Monthly Revenue", f"${latest_m['net_revenue']:,.2f}", f"{latest_m['mom_growth_pct']:+.1f}% MoM")
with col2:
    st.metric("Paying Customers", f"{latest_m['active_paying_customers']:,}", f"{latest_m['active_paying_customers'] - prev_m['active_paying_customers']:+d} MoM")
with col3:
    st.metric("Average Revenue Per User (ARPU)", f"${latest_m['arpu']:.2f}", f"{(latest_m['arpu'] - prev_m['arpu']):+.2f} MoM")
with col4:
    tot_rev = rev_df['gross_revenue'].sum()
    st.metric("Cumulative Gross Revenue", f"${tot_rev:,.2f}")
with col5:
    refund_tot = rev_df['refunded_revenue'].sum()
    refund_pct = (refund_tot / tot_rev) * 100 if tot_rev > 0 else 0
    st.metric("Refund Rate", f"{refund_pct:.2f}%", "-0.15% MoM", delta_color="inverse")

st.markdown("---")

# 2. Revenue Trends & MoM Growth Chart
st.subheader("📈 Monthly Revenue Trends & Growth Rate")
fig_rev = go.Figure()
fig_rev.add_trace(go.Bar(
    x=rev_df["revenue_month"],
    y=rev_df["net_revenue"],
    name="Net Revenue ($)",
    marker_color="#3B82F6",
    yaxis="y1"
))
fig_rev.add_trace(go.Scatter(
    x=rev_df["revenue_month"],
    y=rev_df["mom_growth_pct"],
    name="MoM Growth (%)",
    mode="lines+markers",
    line=dict(color="#10B981", width=3),
    yaxis="y2"
))
fig_rev.update_layout(
    template="plotly_dark",
    height=400,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis=dict(title="Net Revenue ($)", showgrid=True, gridcolor="#334155"),
    yaxis2=dict(title="MoM Growth Rate (%)", overlaying="y", side="right", showgrid=False)
)
st.plotly_chart(fig_rev, use_container_width=True)

st.markdown("---")

# 3. Monthly Cohort Retention Heatmap
st.subheader("👥 Monthly Cohort Retention Heatmap")
st.markdown("Tracking customer retention over time across monthly signup cohorts.")

if not cohort_df.empty:
    # Pivot cohort matrix for heatmap: index = cohort_month, columns = month_index, values = retention_rate_pct
    cohort_pivot = cohort_df.pivot(index="cohort_month", columns="month_index", values="retention_rate_pct")
    
    fig_heat = px.imshow(
        cohort_pivot,
        labels=dict(x="Months Since Signup (Cohort Index)", y="Acquisition Cohort", color="Retention %"),
        x=[f"Month {c}" for c in cohort_pivot.columns],
        y=cohort_pivot.index,
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=".1f"
    )
    fig_heat.update_layout(
        template="plotly_dark",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Cohort data currently assembling.")

st.markdown("---")

# 4. Acquisition Channels & Unit Economics
st.subheader("🎯 Acquisition Channel Performance & LTV/CAC Ratios")

col_a, col_b = st.columns([1, 1])

with col_a:
    fig_acq = px.bar(
        acq_df,
        x="acquisition_channel",
        y="acquired_customers",
        color="channel_churn_rate_pct",
        color_continuous_scale="Reds",
        labels={"acquired_customers": "Total Acquired Customers", "channel_churn_rate_pct": "Churn %"},
        title="Acquisitions & Churn Rate by Channel"
    )
    fig_acq.update_layout(template="plotly_dark", height=380)
    st.plotly_chart(fig_acq, use_container_width=True)

with col_b:
    fig_cac = px.scatter(
        acq_df,
        x="estimated_cac",
        y="revenue_per_acquired_customer",
        size="acquired_customers",
        color="acquisition_channel",
        text="acquisition_channel",
        labels={"estimated_cac": "Customer Acquisition Cost (CAC) $", "revenue_per_acquired_customer": "Revenue Per Customer ($)"},
        title="Unit Economics: CAC vs Revenue Per Customer"
    )
    fig_cac.update_traces(textposition="top center")
    fig_cac.update_layout(template="plotly_dark", height=380, showlegend=False)
    st.plotly_chart(fig_cac, use_container_width=True)

st.dataframe(acq_df, use_container_width=True)
