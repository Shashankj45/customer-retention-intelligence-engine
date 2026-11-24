"""
Page 4: SHAP Model Explainability & Individual Customer Deep-Dive.
Translates black-box ML outputs into transparent, auditable business drivers using TreeSHAP.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.config import MODELS_DIR, PROCESSED_DATA_DIR
from src.database.connection import db_manager
from src.models.explainability import ChurnExplainabilityEngine

st.set_page_config(page_title="SHAP Explainability | Customer Intelligence", page_icon="🔍", layout="wide")

st.title("🔍 Model Explainability & Customer Deep-Dive")
st.markdown("Interpret XGBoost predictions with SHAP (SHapley Additive exPlanations) across global patterns and individual customer profiles.")
st.markdown("---")

# 1. Global Feature Importance
st.subheader("🌐 Global Feature Importance (TreeSHAP)")
st.markdown("Ranked by mean absolute SHAP value: Higher value indicates greater influence on churn risk across the entire customer base.")

shap_path = MODELS_DIR / "shap_global_importance.parquet"
if shap_path.exists():
    imp_df = pd.read_parquet(shap_path).head(12)
    fig_imp = px.bar(
        imp_df.sort_values(by="mean_abs_shap", ascending=True),
        x="mean_abs_shap",
        y="feature",
        orientation="h",
        labels={"mean_abs_shap": "Mean |SHAP Value| (Predictive Impact)", "feature": "Customer Feature"},
        color="mean_abs_shap",
        color_continuous_scale="Viridis"
    )
    fig_imp.update_layout(template="plotly_dark", height=420)
    st.plotly_chart(fig_imp, use_container_width=True)
else:
    st.info("Global SHAP values generating. Run explainability script.")

st.markdown("---")

# 2. Individual Customer Deep-Dive
st.subheader("👤 Individual Customer Diagnostic Profile")
st.markdown("Select an individual customer to inspect their personalized risk factors, protective drivers, and behavioral telemetry.")

# Load candidate customers for dropdown with Caching
@st.cache_data(ttl=3600)
def load_candidate_customers():
    s_df = pd.read_parquet(PROCESSED_DATA_DIR / "churn_scored_customers.parquet")
    c_df = db_manager.execute_query("SELECT customer_id, customer_name, subscription_tier, contract_type, payment_method FROM customers")
    return s_df.merge(c_df, on="customer_id", how="left")

merged = load_candidate_customers()

# Cache the ML Explainer resource
@st.cache_resource
def get_explainer_engine():
    return ChurnExplainabilityEngine()

@st.cache_data(ttl=3600)
def get_cached_customer_explanation(customer_id: str):
    engine = get_explainer_engine()
    return engine.explain_customer(customer_id)

# Top risk candidates at the top of the dropdown
merged_sorted = merged.sort_values(by="churn_probability", ascending=False)
customer_options = [f"{row['customer_id']} - {row['customer_name']} (Churn Prob: {row['churn_probability']:.1%})" for _, row in merged_sorted.iterrows()]

col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    selected_option = st.selectbox("Select Customer to Diagnose:", options=customer_options, index=0)
    selected_id = selected_option.split(" - ")[0]

with col_s2:
    manual_id = st.text_input("Or enter exact Customer ID (e.g. CUST-00042):", "")
    if manual_id.strip():
        selected_id = manual_id.strip().upper()

# Load customer explanation
try:
    explanation = get_cached_customer_explanation(selected_id)
    cust_full = merged[merged["customer_id"] == selected_id].iloc[0]
except Exception as e:
    st.error(f"Could not load explanation for {selected_id}: {e}")
    st.stop()

# Customer Summary Cards
prob = explanation["churn_probability"]
risk_badge = "Critical Risk" if prob >= 0.8 else ("High Risk" if prob >= 0.6 else ("Medium Risk" if prob >= 0.3 else "Low Risk"))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Customer ID & Name", f"{cust_full['customer_id']}", cust_full['customer_name'])
c2.metric("Subscription Tier", cust_full["subscription_tier"], cust_full["contract_type"])
c3.metric("Predicted Churn Probability", f"{prob:.1%}", risk_badge, delta_color="inverse")
c4.metric("Model Baseline (Average Risk)", f"{explanation['base_value']:.1%}")

st.markdown("---")

# 3. SHAP Waterfall Diagnostic Plot
st.subheader(f"📊 Risk Driver Waterfall Decomposition: {cust_full['customer_name']}")
st.markdown("""
- 🔴 **Red Bars (Positive SHAP)**: Factors pushing the customer towards churning (Risk Amplifiers).
- 🟢 **Green Bars (Negative SHAP)**: Factors encouraging the customer to stay (Protective Buffers).
""")

# Top 5 drivers and top 5 protectors
top_drivers = pd.DataFrame(explanation["top_risk_drivers"])
top_protectors = pd.DataFrame(explanation["protective_factors"])
combined_factors = pd.concat([top_drivers, top_protectors]).sort_values(by="shap_value", ascending=True)

if not combined_factors.empty:
    fig_waterfall = go.Figure()
    fig_waterfall.add_trace(go.Bar(
        x=combined_factors["shap_value"],
        y=combined_factors["feature"],
        orientation="h",
        marker=dict(
            color=np.where(combined_factors["shap_value"] > 0, "#EF4444", "#10B981")
        ),
        text=[f"{v:+.3f}" for v in combined_factors["shap_value"]],
        textposition="outside"
    ))
    fig_waterfall.update_layout(
        template="plotly_dark",
        height=450,
        xaxis_title="SHAP Value (Log-Odds Impact on Churn)",
        yaxis_title="Observed Behavioral Feature",
        margin=dict(l=20, r=40, t=20, b=20)
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

# Diagnostic Summary Table
col_d1, col_d2 = st.columns(2)
with col_d1:
    st.markdown("### ⚠️ Top 5 Risk Drivers (Why they might churn)")
    st.dataframe(top_drivers[["feature", "shap_value", "feature_value"]], use_container_width=True)

with col_d2:
    st.markdown("### 🛡️ Top Protective Factors (Why they might stay)")
    st.dataframe(top_protectors[["feature", "shap_value", "feature_value"]], use_container_width=True)
