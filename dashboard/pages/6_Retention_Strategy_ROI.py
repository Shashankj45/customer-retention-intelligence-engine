"""
Page 6: Retention Optimization & ROI Simulator.
Prescriptive intervention strategy assignment and interactive what-if financial ROI scenario simulator.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.config import PROCESSED_DATA_DIR
from src.retention.roi_simulator import RetentionROISimulator

st.set_page_config(page_title="Retention Strategy & ROI | Customer Intelligence", page_icon="💡", layout="wide")

st.title("💡 Retention Strategy & ROI Simulator")
st.markdown("Prescribe personalized interventions, estimate revenue saved, and simulate marketing campaign returns.")
st.warning("🧪 **SIMULATION ASSUMPTION NOTICE**: All metrics, saved revenue estimates, and ROI projections on this page represent simulated what-if scenario modeling based on synthetic benchmark data and explicit business assumptions (outreach cost, discount concession, and acceptance elasticity). They demonstrate retention optimization methodology and must not be interpreted as audited historical revenue.")
st.markdown("---")

@st.cache_data(ttl=3600)
def load_retention_recommendations():
    rec_path = PROCESSED_DATA_DIR / "retention_recommendations.parquet"
    if not rec_path.exists():
        from src.retention.decision_engine import RetentionDecisionEngine
        return RetentionDecisionEngine().generate_recommendations()
    return pd.read_parquet(rec_path)

rec_df = load_retention_recommendations()

# Top Strategy Summary
total_opp = rec_df["expected_saved_revenue"].sum()
total_cost = rec_df["estimated_retention_cost"].sum()
net_opp = rec_df["estimated_net_roi"].sum()
overall_roi = (net_opp / max(1.0, total_cost)) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Recommended Interventions", f"{len(rec_df):,}")
c2.metric("Gross Saved Revenue [Simulated]", f"${total_opp:,.2f}")
c3.metric("Outreach Investment [Simulated]", f"${total_cost:,.2f}")
c4.metric("Net Economic Benefit [Simulated]", f"${net_opp:,.2f}", f"{overall_roi:.1f}% ROI")

st.markdown("---")

# 1. Interactive What-If ROI Simulator
st.subheader("🧮 Interactive What-If Retention ROI Simulator")
st.markdown("Simulate different campaign designs, budget allocations, and discount concessions in real-time.")

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    st.markdown("#### ⚙️ Scenario Parameters")
    sel_tiers = st.multiselect(
        "Target Risk Tiers:",
        ["Critical Risk", "High Risk", "Medium Risk", "Low Risk"],
        default=["Critical Risk", "High Risk"]
    )
    contact_cost = st.slider("Outreach Cost per Customer ($):", 5.0, 150.0, 25.0, 5.0)
    discount_pct = st.slider("Discount Incentive Offered (%):", 0.0, 30.0, 15.0, 1.0)
    acceptance_rate = st.slider("Campaign Acceptance Rate (%):", 10.0, 80.0, 45.0, 5.0)
    min_clv = st.number_input("Minimum CLV Filter ($):", 0.0, 10000.0, 0.0, 250.0)

simulator = RetentionROISimulator()
sim_results = simulator.run_simulation(
    targeted_tiers=sel_tiers,
    contact_cost_per_user=contact_cost,
    discount_percent=discount_pct,
    acceptance_rate_percent=acceptance_rate,
    min_clv_threshold=min_clv
)

with sim_col2:
    st.markdown("#### 📊 Simulation Results")
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Targeted Accounts", f"{sim_results['targeted_customers']:,}")
    r2.metric("Accounts Retained", f"{sim_results['retained_customers']:,}", f"{(sim_results['retained_customers']/max(1, sim_results['targeted_customers']))*100:.1f}% Yield")
    r3.metric("Gross Revenue Saved", f"${sim_results['gross_revenue_saved']:,.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Total Campaign Cost", f"${sim_results['total_campaign_cost']:,.2f}")
    r5.metric("Net Profit Retained", f"${sim_results['net_profit_saved']:,.2f}", f"{sim_results['roi_percentage']:+.1f}% ROI")
    r6.metric("Payback Duration", f"{sim_results['payback_months']:.1f} Months", "Capital Breakeven")

    # Financial Waterfall Chart
    fig_waterfall = go.Figure(go.Waterfall(
        name="Financial Impact",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Gross Revenue Saved", "Outreach Operations", "Discount Incentives", "Net Economic Benefit"],
        y=[
            sim_results["gross_revenue_saved"],
            -sim_results["outreach_cost"],
            -sim_results["discount_cost"],
            sim_results["net_profit_saved"]
        ],
        connector={"line": {"color": "#64748B"}},
        decreasing={"marker": {"color": "#EF4444"}},
        increasing={"marker": {"color": "#10B981"}},
        totals={"marker": {"color": "#3B82F6"}}
    ))
    fig_waterfall.update_layout(template="plotly_dark", height=320, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_waterfall, use_container_width=True)

st.markdown("---")

# 2. Prescribed Retention Strategy Distribution
st.subheader("📋 Recommended Action Catalog")
col_s1, col_s2 = st.columns([1, 1])

with col_s1:
    strat_counts = rec_df["recommended_strategy"].value_counts().reset_index()
    strat_counts.columns = ["strategy", "count"]
    fig_strat = px.bar(
        strat_counts,
        x="count",
        y="strategy",
        orientation="h",
        color="count",
        color_continuous_scale="Teal",
        labels={"count": "Number of Customers", "strategy": "Recommended Action"}
    )
    fig_strat.update_layout(template="plotly_dark", height=380, showlegend=False)
    st.plotly_chart(fig_strat, use_container_width=True)

with col_s2:
    chan_counts = rec_df["intervention_channel"].value_counts().reset_index()
    chan_counts.columns = ["channel", "count"]
    fig_chan = px.pie(
        chan_counts,
        names="channel",
        values="count",
        hole=0.45,
        title="Intervention Channels Breakdown"
    )
    fig_chan.update_layout(template="plotly_dark", height=380)
    st.plotly_chart(fig_chan, use_container_width=True)

st.markdown("---")

# 3. Actionable Customer Recommendations Table
st.subheader("🎯 Prioritized Outreach Roster (Ranked by Net ROI)")
st.dataframe(
    rec_df[[
        "priority_rank", "customer_name", "risk_tier", "clv_tier",
        "recommended_strategy", "intervention_channel", "estimated_retention_cost",
        "expected_saved_revenue", "estimated_net_roi"
    ]].head(250),
    use_container_width=True,
    height=400
)
st.caption("Displaying top 250 highest-ROI retention opportunities.")

with st.expander("ℹ️ Simulation Assumptions, Mathematical Framework & Sensitivity Limits"):
    st.markdown("""
    ### 🔬 Methodology & Economic Assumptions
    
    1. **Counterfactual Baseline**:
       - Without intervention, a customer's probability of churn is given by the XGBoost estimate $\hat{p} \in [0, 1]$.
       - Expected revenue loss without intervention: $\mathbb{E}[\text{Loss}] = \hat{p} \times \text{Projected CLV}_{12M}$.
    
    2. **Intervention Efficacy & Acceptance Elasticity**:
       - When targeted, an intervention carries an empirical success probability $\eta \in [0.30, 0.65]$ depending on contract type and tier.
       - Expected revenue saved: $\mathbb{E}[\text{Saved}] = \hat{p} \times \text{Projected CLV}_{12M} \times \eta$.
    
    3. **Cost Structure**:
       - Total Campaign Cost = $\sum (\text{Channel Outreach Cost} + \text{Discount Incentive Cost})$.
       - Outreach cost varies by touchpoint: Automated Email ($15), Priority Support Queue ($25), CS Executive Outreach ($75), Concierge White-Glove Onboarding ($120).
    
    4. **Net Economic Benefit & Payback**:
       - $\text{Net Benefit} = \mathbb{E}[\text{Saved}] - \text{Total Cost}$.
       - $\text{ROI} = (\text{Net Benefit} / \text{Total Cost}) \times 100\%$.
    
    > **Governance Note**: These simulations provide directional guidance for retention budget allocation. In production environments, parameter estimates should be calibrated using randomized controlled trials (A/B testing holdout groups).
    """)
