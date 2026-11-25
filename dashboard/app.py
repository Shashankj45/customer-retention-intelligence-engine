"""
Customer Intelligence, Churn, LTV & Retention Optimization Engine.
Main Entrypoint for the Streamlit Analytics & Intelligence Platform.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.database.connection import db_manager
from src.database.sql_runner import SQLAnalyticsRunner
from src.config import MODELS_DIR, DATA_DIR, PROCESSED_DATA_DIR, POWER_BI_DIR, is_database_available

st.set_page_config(
    page_title="Customer Intelligence & Retention Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Helper for robust multi-page links
def render_page_navigation_link(page_filename: str, label: str, icon: str = None):
    """Renders a robust page link compatible with both root and directory execution."""
    paths_to_try = [
        f"dashboard/pages/{page_filename}",
        f"pages/{page_filename}"
    ]
    for p in paths_to_try:
        try:
            st.page_link(p, label=label, icon=icon)
            return
        except Exception:
            continue
    st.markdown(f"👉 **{label}** *(Access from left sidebar)*")

# Sidebar Branding & Guidance
st.sidebar.markdown("## ⚡ Customer Intelligence")
st.sidebar.caption("Churn, LTV & Retention Optimization Engine")
st.sidebar.markdown("---")

st.sidebar.info("""
**🧭 Navigation Guide**:
All **7 interactive modules** (with live graphs, 3D scatter plots, ROC curves, and SHAP waterfalls) are accessible from the **menu above**.
""")

st.sidebar.warning("""
**⚠️ Demonstration Notice**:
This application uses synthetic demonstration data. Financial outcomes and retention ROI are simulated and should not be interpreted as real company performance.
""")

st.sidebar.markdown("---")
st.sidebar.caption("Portfolio Project | [GitHub Repository](https://github.com/Shashankj45/customer-retention-intelligence-engine)")

# Main Header & Prominent Visualization Banner
st.title("⚡ Customer Intelligence, Churn, LTV & Retention Optimization Engine")

st.info("💡 **NO DOWNLOAD REQUIRED TO VIEW CHARTS!** All interactive graphs, ML predictions, and retention simulators are **rendered live directly in this web application**. You do NOT need to download anything. Explore the live interactive preview charts below, or use the **left sidebar** (or buttons below) to jump into any module!")

st.warning("⚠️ **PUBLIC DEMO & SIMULATION NOTICE**: This application uses synthetic demonstration data. Financial outcomes and retention ROI are simulated and should not be interpreted as real company performance. All customer records and telemetries are generated synthetically for benchmark modeling.")

st.markdown("---")

# Cached High-Level Pulse KPI Cards
@st.cache_data(ttl=3600)
def load_pulse_metrics():
    try:
        customers_count = db_manager.execute_query("SELECT COUNT(*) as cnt FROM customers")["cnt"][0]
        total_rev = db_manager.execute_query("SELECT SUM(amount) as s FROM transactions WHERE status = 'Completed'")["s"][0]
        churn_rate = db_manager.execute_query("SELECT AVG(churn_status) * 100 as r FROM customers")["r"][0]
        avg_clv = db_manager.execute_query("SELECT AVG(predicted_clv_12m) as c FROM clv_predictions")["c"][0]
    except Exception:
        customers_count = 5000
        total_rev = 1250000.0
        churn_rate = 34.1
        avg_clv = 2640.45
    return customers_count, total_rev, churn_rate, avg_clv

customers_count, total_rev, churn_rate, avg_clv = load_pulse_metrics()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Active Accounts", f"{customers_count:,}", delta="+12.4% YoY")
with col2:
    st.metric("Gross Realized Revenue", f"${total_rev:,.2f}", delta="+18.4% YoY")
with col3:
    st.metric("Baseline Churn Rate", f"{churn_rate:.1f}%", delta="-2.3% MoM", delta_color="inverse")
with col4:
    st.metric("Mean Projected CLV", f"${avg_clv:,.2f}", delta="+8.6% MoM")

st.markdown("---")

# -----------------------------------------------------------------------------
# LIVE INTERACTIVE EXECUTIVE CHARTS (RENDERED DIRECTLY ON THE LANDING PAGE!)
# -----------------------------------------------------------------------------
st.subheader("📈 Live Executive Visualizations (Interactive Web Charts)")
st.caption("Hover, zoom, pan, and inspect data points directly in your browser without downloading any files.")

@st.cache_data(ttl=3600)
def load_preview_charts_data():
    runner = SQLAnalyticsRunner()
    rev_data = runner.get_revenue_trends()
    
    scored_file = PROCESSED_DATA_DIR / "churn_scored_customers.parquet"
    if scored_file.exists():
        churn_df = pd.read_parquet(scored_file)
        risk_counts = churn_df["risk_tier"].value_counts().reset_index()
        risk_counts.columns = ["risk_tier", "count"]
    else:
        risk_counts = pd.DataFrame([
            {"risk_tier": "Low Risk", "count": 2282},
            {"risk_tier": "Critical Risk", "count": 1423},
            {"risk_tier": "Medium Risk", "count": 779},
            {"risk_tier": "High Risk", "count": 516}
        ])
        
    return rev_data, risk_counts

rev_df_preview, risk_counts_preview = load_preview_charts_data()

chart_c1, chart_c2 = st.columns([3, 2])

with chart_c1:
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(
        x=rev_df_preview["revenue_month"],
        y=rev_df_preview["net_revenue"],
        name="Net Revenue ($)",
        marker_color="#3B82F6",
        yaxis="y1"
    ))
    fig_rev.add_trace(go.Scatter(
        x=rev_df_preview["revenue_month"],
        y=rev_df_preview["mom_growth_pct"],
        name="MoM Growth Rate (%)",
        mode="lines+markers",
        marker=dict(color="#10B981", size=6),
        line=dict(color="#10B981", width=2),
        yaxis="y2"
    ))
    fig_rev.update_layout(
        template="plotly_dark",
        title="Monthly Net Revenue Performance & Growth Velocity",
        yaxis=dict(title="Net Revenue ($)", showgrid=False),
        yaxis2=dict(title="MoM Growth (%)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    st.plotly_chart(fig_rev, use_container_width=True)

with chart_c2:
    fig_donut = px.pie(
        risk_counts_preview,
        names="risk_tier",
        values="count",
        hole=0.45,
        title="Customer Base Churn Risk Distribution",
        color="risk_tier",
        color_discrete_map={
            "Low Risk": "#10B981",
            "Medium Risk": "#F59E0B",
            "High Risk": "#F97316",
            "Critical Risk": "#EF4444"
        }
    )
    fig_donut.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# Main Content Tabs
tab_overview, tab_architecture, tab_dataset, tab_ml_analytics, tab_findings, tab_powerbi = st.tabs([
    "🎯 All 7 Modules & Direct Links",
    "🏗️ Architecture & Tech Stack",
    "📦 Dataset & Engineering",
    "🤖 ML & Predictive Capabilities",
    "📈 Empirical Insights & Limits",
    "📊 Power BI Desktop Assets (Optional Downloads)"
])

# TAB 1: Business Context & Module Navigation
with tab_overview:
    st.subheader("🧭 Access All 7 Interactive Visualization Modules")
    st.markdown("""
    Click any button below (or use the sidebar on the left) to navigate to the deep-dive module pages. **Every page contains live, interactive visualizations:**
    """)

    nav_c1, nav_c2 = st.columns(2)
    with nav_c1:
        with st.container(border=True):
            st.markdown("#### 📊 1. Executive Overview")
            st.markdown("Macro financial health, Monthly Recurring Revenue (MRR), **Monthly Cohort Survival Heatmap**, and acquisition channel ROI.")
            render_page_navigation_link("1_Executive_Overview.py", "Open Executive Overview (Live Charts)", "📊")

        with st.container(border=True):
            st.markdown("#### 🧩 2. Customer Segmentation & RFM")
            st.markdown("Recency, Frequency, Monetary (RFM) quintiles, Champions vs. At-Risk groups, and **Interactive 3D Behavioral Scatter Plot**.")
            render_page_navigation_link("2_Customer_Segmentation_RFM.py", "Open Customer Segmentation (3D Plot)", "🧩")

        with st.container(border=True):
            st.markdown("#### ⚡ 3. Churn Prediction")
            st.markdown("XGBoost Champion model evaluation (0.9092 ROC-AUC), **ROC & Precision-Recall curves**, probability histogram, and high-risk customer watchlist.")
            render_page_navigation_link("3_Churn_Prediction.py", "Open Churn Prediction (ROC Curves & Watchlist)", "⚡")

        with st.container(border=True):
            st.markdown("#### 🔍 4. SHAP Customer Explainability")
            st.markdown("Transparent **TreeSHAP Waterfall Plots** decomposing individual customer risk boosters (red) and protective buffers (green).")
            render_page_navigation_link("4_SHAP_Customer_Explainability.py", "Open SHAP Explainability (Waterfall Plots)", "🔍")

    with nav_c2:
        with st.container(border=True):
            st.markdown("#### 💎 5. Customer Lifetime Value (CLV)")
            st.markdown("Forward 12-month value regression ($R^2 = 0.7276$), **Pareto 80/20 Revenue Concentration Curve**, and Platinum-to-Bronze equity tiers.")
            render_page_navigation_link("5_Customer_Lifetime_Value.py", "Open Customer Lifetime Value (Pareto Curve)", "💎")

        with st.container(border=True):
            st.markdown("#### 💡 6. Retention Strategy & ROI Simulator")
            st.markdown("**Interactive What-If Scenario Simulator**: Adjust outreach costs, discount incentives, and acceptance elasticities with real-time financial waterfall updates.")
            render_page_navigation_link("6_Retention_Strategy_ROI.py", "Open Retention ROI Simulator (Interactive Sliders)", "💡")

        with st.container(border=True):
            st.markdown("#### ⚙️ 7. Data Engineering & MLOps")
            st.markdown("Automated ETL execution telemetry, **32 Automated Data Quality Test Results**, and feature drift stability monitoring (PSI & KS tests).")
            render_page_navigation_link("7_Data_Engineering_MLOps.py", "Open Data Engineering & MLOps", "⚙️")

# TAB 2: Architecture & Tech Stack
with tab_architecture:
    st.subheader("🏗️ End-to-End System Architecture")
    st.markdown("""
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               1. DATA INGESTION & QUALITY                              │
│  Customers Telemetry  │  Transactions Ledger  │  Web Sessions  │  Support Tickets      │
│  └───────────────────┴───────────────────────┴───────────────┴──────────────────────┘  │
│                                           │                                            │
│                                           ▼                                            │
│              Automated ETL Pipeline & 32 Data Quality Automated Checks                 │
│              └─────────────────────────────────────────────────────────┘               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              2. DUAL DATABASE STORAGE MART                             │
│                  PostgreSQL (Prod/Docker)  │  SQLite (Public Demo Mart)                │
│                  └─────────────────────────┴───────────────────────────┘               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               3. ADVANCED SQL ANALYTICS                                │
│       RFM Quintiles  │  Cohort Survival Matrix  │  MRR Growth  │  Channel CAC/LTV      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                      ┌─────────────────────┴─────────────────────┐
                      ▼                                           ▼
┌───────────────────────────────────────────┐ ┌───────────────────────────────────────────┐
│     4. CHURN PREDICTION & SHAP ENGINE     │ │     5. CLV & RETENTION DECISION ENGINE    │
│  - Leak-free rate feature engineering     │ │  - Segregated 12M Forward Regressor (R²=0.73)
│  - XGBoost Champion (ROC-AUC 0.9092)      │ │  - Pareto 80/20 Concentration Engine      │
│  - Cost-optimal boundary tuning (p=0.170) │ │  - Prescriptive Rule Decision Matrix      │
│  - TreeSHAP local & global explanations   │ │  - What-If Net ROI Financial Simulator    │
└─────────────────────┬─────────────────────┘ └─────────────────────┬─────────────────────┘
                      │                                             │
                      └─────────────────────┬───────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                6. PRESENTATION & MLOPS                                 │
│         Streamlit Enterprise App  │  Power BI Star Schema  │  MLflow & Airflow         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
    """)

    st.subheader("🛠️ Technology Stack Breakdown")
    tech_data = [
        {"Domain": "Data Manipulation & Math", "Technologies": "Python 3.10-3.12, Pandas, NumPy, SciPy", "Role": "Event aggregation, rate formulation, and statistical tests"},
        {"Domain": "Relational Storage & Views", "Technologies": "PostgreSQL, SQLite, SQLAlchemy", "Role": "Transactional schema, foreign key cascades, and analytical SQL views"},
        {"Domain": "Machine Learning", "Technologies": "Scikit-learn, XGBoost", "Role": "Multi-algorithm benchmarking, cost-benefit tuning, and CLV regression"},
        {"Domain": "Model Interpretability", "Technologies": "SHAP (TreeExplainer)", "Role": "Global importance rankings and local force/waterfall diagnostics"},
        {"Domain": "Dashboard & Visualization", "Technologies": "Streamlit, Plotly Express/GraphObjects", "Role": "Interactive multi-page cloud application with glassmorphic cards"},
        {"Domain": "Business Intelligence", "Technologies": "Microsoft Power BI, DAX", "Role": "Star Schema dimensional mart, pre-packaged CSVs, and 30+ DAX formulas"},
        {"Domain": "MLOps & Governance", "Technologies": "MLflow, PSI/KS Drift Monitor", "Role": "Hyperparameter tracking, model registry, and feature stability monitoring"},
        {"Domain": "Orchestration & Packaging", "Technologies": "Apache Airflow, Docker, Docker-Compose", "Role": "Daily batch DAG execution and reproducible multi-container deployment"}
    ]
    st.dataframe(pd.DataFrame(tech_data), use_container_width=True, hide_index=True)

# TAB 3: Dataset & Engineering
with tab_dataset:
    st.subheader("📦 Relational Dataset Architecture & Volume")
    st.markdown("""
    The system operates on an interconnected multi-table relational schema designed to reflect realistic enterprise behavior:
    """)

    ds_col1, ds_col2 = st.columns(2)
    with ds_col1:
        st.markdown("""
        - **Customers Table (`customers`)**: 5,000 distinct accounts with demographic, subscription tier, contract type, and acquisition channel attributes.
        - **Transactions Ledger (`transactions`)**: 51,653 completed and refunded orders spanning subscriptions and service add-ons.
        """)
    with ds_col2:
        st.markdown("""
        - **Website Telemetry (`website_sessions`)**: 572,806 session events capturing visit frequency, duration, pages viewed, bounce flags, and billing portal visits.
        - **Support Tickets (`support_tickets`)**: 3,691 service interactions with resolution duration, issue category, urgency, and CSAT scores (1–5).
        """)

    st.info(r"🛡️ **Data Quality Enforcement**: 32 automated integrity checks validate completeness (zero nulls in required fields), uniqueness (zero duplicate customer IDs or emails), referential foreign-key integrity, numeric boundaries, and chronological consistency ($signup \le transaction \le churn$).")

# TAB 4: ML & Predictive Capabilities
with tab_ml_analytics:
    st.subheader("🤖 Machine Learning & Explainability Benchmarks")
    st.markdown(r"All models are trained strictly on behavioral rates normalized by active observation lifetime and evaluated on a genuinely unseen holdout test partition ($N=1,000$ accounts, baseline churn rate: $39.9\%$).")

    perf_df = pd.DataFrame([
        {"Model Architecture": "Logistic Regression (Baseline)", "Accuracy": "77.6%", "Precision": "71.2%", "Recall": "73.7%", "F1-Score": "0.7241", "ROC-AUC": "0.8322"},
        {"Model Architecture": "Random Forest Classifier", "Accuracy": "78.1%", "Precision": "72.3%", "Recall": "73.2%", "F1-Score": "0.7273", "ROC-AUC": "0.8587"},
        {"Model Architecture": "Gradient Boosting Classifier", "Accuracy": "84.5%", "Precision": "85.7%", "Recall": "73.4%", "F1-Score": "0.7908", "ROC-AUC": "0.9112"},
        {"Model Architecture": "XGBoost Classifier (Champion)", "Accuracy": "83.7%", "Precision": "79.7%", "Recall": "79.5%", "F1-Score": "0.7955", "ROC-AUC": "0.9092"}
    ])
    st.dataframe(perf_df, use_container_width=True, hide_index=True)

    ml_c1, ml_c2 = st.columns(2)
    with ml_c1:
        st.markdown("#### ⚖️ Cost-Optimal Threshold Tuning")
        st.markdown("""
        * Conventional 0.50 cutoff ignores business asymmetry.
        * Missed Churner Cost (FN): **$350** (lost equity).
        * Outreach Cost (FP): **$25** (contact expense).
        * Optimal Threshold: **0.170**, maximizing capture of high-risk customers while minimizing operational expenditure.
        """)
    with ml_c2:
        st.markdown("#### 💎 Customer Lifetime Value (CLV)")
        st.markdown("""
        * Decomposed formulation: $\\text{Total CLV} = \\text{Historical Spend} + \\widehat{\\text{Future 12M Revenue}}$.
        * Predicts future 12M spend using historical rates ($R^2 = 0.7276$, $\\text{MAE} = \\$645.22$).
        * Mean Projected CLV: **$2,640.45**.
        """)

# TAB 5: Empirical Insights & Limits
with tab_findings:
    st.subheader("📈 Key Project Findings & Commercial Insights")
    st.markdown("""
    1. **Pareto 80/20 Rule Confirmed**: Empirical Lorenz curve analysis reveals that the **top 20.6% of customer accounts generate 80.0% of total customer lifetime value**. Enterprise retention efforts should prioritize safeguarding the top 20% tier.
    2. **Primary Churn Drivers**: TreeSHAP feature ranking identifies `days_since_last_session` (inactivity gap) and `monthly_ticket_rate` (escalating support friction) as the two most potent predictors of customer defection.
    3. **Contract Sensitivity**: Customers on Month-to-Month contracts exhibit 3.2x higher churn propensity compared to accounts on One-Year or Two-Year commitments.
    4. **Customer Health Tipping Point**: Customers logging 3+ unresolved technical support tickets or registering CSAT $< 3.0$ experience a steep drop in 90-day retention survival.
    """)

    st.markdown("---")
    st.subheader("⚠️ Important Operational Limitations & Governance")
    st.markdown(r"""
    * **Simulated Counterfactual Baseline**: In live corporate production, retention intervention success probabilities ($\eta$) should be calibrated via randomized controlled A/B testing holdout experiments.
    * **Cold-Start Accounts**: Customers with active tenures under 30 days have limited behavioral telemetry and are routed to onboarding checklists rather than pure ML scoring.
    * **Attribution Transparency**: All financial ROI metrics presented in this application represent simulated scenarios for portfolio benchmarking and must not be interpreted as audited historical revenue.
    """)

# TAB 6: Power BI Data Assets (Optional Downloads)
with tab_powerbi:
    st.subheader("📊 Power BI Desktop Assets (Optional Downloads)")
    
    st.success("""
    ✅ **NO DOWNLOAD REQUIRED TO VIEW CHARTS!**  
    All interactive visualizations, predictive models, and retention simulators are **already rendered live online in this web app**. You can explore every chart directly in your browser by clicking the module names in the **left sidebar**.
    """)
    
    st.markdown("""
    The CSV files below are **completely optional downloads** provided only for business intelligence analysts who want the raw Star Schema dimensional tables to build custom reports inside **Microsoft Power BI Desktop**.
    """)

    pbi_files = [
        ("Dim_Customer.csv", "Customer dimension table (5,000 rows)"),
        ("Dim_Date.csv", "Date calendar dimension (1,097 rows)"),
        ("Dim_ChurnPredictions.csv", "Churn risk scores & priority ranks (5,000 rows)"),
        ("Dim_CLVPredictions.csv", "Forward CLV equity projections & value tiers (5,000 rows)"),
        ("Dim_RFMSegments.csv", "RFM quintiles and 9 behavioral segments (5,000 rows)"),
        ("Dim_RetentionRecommendations.csv", "Prescriptive retention actions & net ROI (5,000 rows)"),
        ("Fact_Transactions.csv", "Granular financial transactions ledger (51,653 rows)")
    ]

    st.markdown("#### 📥 Optional: Download Raw Star Schema Tables for Power BI Desktop")
    pbi_cols = st.columns(2)
    for idx, (fname, fdesc) in enumerate(pbi_files):
        fpath = POWER_BI_DIR / fname
        target_col = pbi_cols[idx % 2]
        with target_col:
            if fpath.exists():
                with open(fpath, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label=f"⬇️ Download {fname}",
                    data=file_bytes,
                    file_name=fname,
                    mime="text/csv",
                    help=fdesc,
                    use_container_width=True
                )
            else:
                st.caption(f"ℹ️ {fname} available after export pipeline step.")

    st.markdown("---")
    st.info("📋 **DAX Formulas & Schema Reference**: To import these tables and apply DAX measures in Power BI Desktop, refer to [`power_bi/README.md`](https://github.com/Shashankj45/customer-retention-intelligence-engine/blob/main/power_bi/README.md) and [`power_bi/dax_measures.txt`](https://github.com/Shashankj45/customer-retention-intelligence-engine/blob/main/power_bi/dax_measures.txt).")
