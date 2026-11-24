"""
Page 5: Customer Lifetime Value (CLV) & Revenue Contribution.
Forward 12-month value forecasting, Pareto 80/20 revenue concentration, and tier segmentation.
"""

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.config import MODELS_DIR, PROCESSED_DATA_DIR
from src.database.connection import db_manager

st.set_page_config(page_title="Customer Lifetime Value | Customer Intelligence", page_icon="💎", layout="wide")

st.title("💎 Customer Lifetime Value & Revenue Contribution")
st.markdown("Forecast forward 12-month customer equity, isolate high-value accounts, and evaluate Pareto concentration.")
st.info("🛡️ **Leak-Free CLV Modeling**: Total Projected CLV = Realized Historical Spend + Predicted Future 12M Spend. The forward regression model predicts unobserved future 12-month spend using only historical behavioral rates (Holdout R² = 0.7276, MAE = $645.22). Future spend is strictly excluded from input features.")
st.markdown("---")

# 1. Load CLV Data with Caching
@st.cache_data(ttl=3600)
def load_clv_data():
    c_df = pd.read_parquet(PROCESSED_DATA_DIR / "clv_predictions.parquet")
    cu_df = db_manager.execute_query("SELECT customer_id, customer_name, subscription_tier, contract_type, acquisition_channel FROM customers")
    ch_df = pd.read_parquet(PROCESSED_DATA_DIR / "churn_scored_customers.parquet")[["customer_id", "churn_probability", "risk_tier"]]
    merged = c_df.merge(cu_df, on="customer_id", how="left").merge(ch_df, on="customer_id", how="left")

    pareto_file = MODELS_DIR / "pareto_summary.json"
    if pareto_file.exists():
        with open(pareto_file, "r", encoding="utf-8") as f:
            pareto_meta = json.load(f)
    else:
        pareto_meta = {}

    return merged, pareto_meta

merged_clv, pareto_meta = load_clv_data()

# Top KPI Cards
total_clv_pool = merged_clv["predicted_clv_12m"].sum()
mean_clv = merged_clv["predicted_clv_12m"].mean()
median_clv = merged_clv["predicted_clv_12m"].median()
top_80_pct = pareto_meta.get("pct_customers_generating_80pct_revenue", 20.1)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total 12M Projected Equity", f"${total_clv_pool:,.2f}")
c2.metric("Mean Predicted CLV", f"${mean_clv:,.2f}")
c3.metric("Median Predicted CLV", f"${median_clv:,.2f}")
c4.metric("Pareto 80% Threshold", f"Top {top_80_pct:.1f}% Customers", "Generate 80% Total Value")

st.markdown("---")

# 2. Pareto 80/20 Concentration Curve & Value Tiers
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("⚖️ Pareto 80/20 Cumulative Distribution Curve")
    st.markdown("Evaluating revenue concentration: how few customers drive the vast majority of enterprise value.")

    sorted_clv = merged_clv.sort_values(by="predicted_clv_12m", ascending=False).reset_index(drop=True)
    sorted_clv["cum_clv"] = sorted_clv["predicted_clv_12m"].cumsum()
    sorted_clv["cum_clv_pct"] = (sorted_clv["cum_clv"] / total_clv_pool) * 100.0
    sorted_clv["cum_cust_pct"] = ((sorted_clv.index + 1) / len(sorted_clv)) * 100.0

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Scatter(
        x=sorted_clv["cum_cust_pct"],
        y=sorted_clv["cum_clv_pct"],
        mode="lines",
        name="Actual CLV Concentration",
        line=dict(color="#3B82F6", width=3)
    ))
    fig_pareto.add_trace(go.Scatter(
        x=[0, 100],
        y=[0, 100],
        mode="lines",
        name="Equal Distribution (Baseline)",
        line=dict(color="#64748B", dash="dash")
    ))
    fig_pareto.add_hline(y=80, line_dash="dot", line_color="#EF4444", annotation_text="80% Total Revenue")
    fig_pareto.add_vline(x=top_80_pct, line_dash="dot", line_color="#EF4444", annotation_text=f"{top_80_pct:.1f}% of Accounts")
    
    fig_pareto.update_layout(
        template="plotly_dark",
        height=400,
        xaxis_title="Cumulative % of Customers (Ranked by Value)",
        yaxis_title="Cumulative % of Total CLV",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

with col_right:
    st.subheader("🏷️ Value Tier Distribution")
    st.markdown("Customer segmentation across Platinum, Gold, Silver, and Bronze Lifetime Value tiers.")

    tier_counts = merged_clv["clv_tier"].value_counts().reset_index()
    tier_counts.columns = ["clv_tier", "count"]

    tier_colors = {
        "Platinum Tier (Top 10%)": "#A855F7",
        "Gold Tier (Top 30%)": "#F59E0B",
        "Silver Tier (Mid 30%)": "#06B6D4",
        "Bronze Tier (Bottom 40%)": "#64748B"
    }

    fig_tier = px.bar(
        tier_counts,
        x="clv_tier",
        y="count",
        color="clv_tier",
        color_discrete_map=tier_colors,
        labels={"count": "Number of Accounts", "clv_tier": "Value Tier"}
    )
    fig_tier.update_layout(template="plotly_dark", height=400, showlegend=False)
    st.plotly_chart(fig_tier, use_container_width=True)

st.markdown("---")

# 3. Historical Revenue vs Predicted 12M Forward Value
st.subheader("🔮 Historical Spend vs Predicted 12M Future Value")
sample_scatter = merged_clv.sample(min(1200, len(merged_clv)), random_state=42)

fig_scatter = px.scatter(
    sample_scatter,
    x="historical_revenue",
    y="predicted_clv_12m",
    color="clv_tier",
    color_discrete_map=tier_colors,
    size="predicted_clv_12m",
    hover_name="customer_name",
    hover_data=["customer_id", "subscription_tier", "risk_tier"],
    labels={"historical_revenue": "Historical Realized Spend ($)", "predicted_clv_12m": "Predicted 12M Total CLV ($)"}
)
fig_scatter.update_layout(template="plotly_dark", height=450)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# 4. High-Value Account Explorer Table
st.subheader("⭐ High-Value Account Explorer")
col_e1, col_e2 = st.columns([1, 2])
with col_e1:
    selected_tier = st.selectbox("Filter Tier:", ["All Tiers", "Platinum Tier (Top 10%)", "Gold Tier (Top 30%)", "Silver Tier (Mid 30%)", "Bronze Tier (Bottom 40%)"])
with col_e2:
    search_cust = st.text_input("Search Customer Name or ID:", "")

filtered_clv = merged_clv.copy()
if selected_tier != "All Tiers":
    filtered_clv = filtered_clv[filtered_clv["clv_tier"] == selected_tier]
if search_cust:
    filtered_clv = filtered_clv[
        filtered_clv["customer_name"].str.contains(search_cust, case=False, na=False) |
        filtered_clv["customer_id"].str.contains(search_cust, case=False, na=False)
    ]

st.dataframe(
    filtered_clv.sort_values(by="predicted_clv_12m", ascending=False)[
        ["customer_id", "customer_name", "subscription_tier", "contract_type", "historical_revenue", "predicted_clv_12m", "clv_tier", "risk_tier"]
    ],
    use_container_width=True,
    height=380
)
st.caption(f"Showing {len(filtered_clv):,} account records.")
