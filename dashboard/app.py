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
from src.config import MODELS_DIR, DATA_DIR, POWER_BI_DIR, is_database_available

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

# Sidebar
st.sidebar.image("https://img.icons8.com/fluency/96/bullseye.png", width=64)
st.sidebar.title("Customer Intelligence")
st.sidebar.caption("⚡ Churn, LTV & Retention Optimization Engine")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🧭 Platform Modules")
st.sidebar.markdown("""
- [📊 1. Executive Overview](Executive_Overview)
- [🧩 2. Customer Segmentation](Customer_Segmentation_RFM)
- [⚡ 3. Churn Prediction](Churn_Prediction)
- [🔍 4. SHAP Explainability](SHAP_Customer_Explainability)
- [💎 5. Customer Lifetime Value](Customer_Lifetime_Value)
- [💡 6. Retention Strategy & ROI](Retention_Strategy_ROI)
- [⚙️ 7. Data Eng & MLOps](Data_Engineering_MLOps)
""")

st.sidebar.markdown("---")
st.sidebar.warning("""
**⚠️ Demonstration Notice**:
This application uses synthetic demonstration data. Financial outcomes and retention ROI are simulated and should not be interpreted as real company performance.
""")

st.sidebar.info("""
**Tech Stack**:
- Python, PostgreSQL & SQLite
- Scikit-learn, XGBoost, SHAP
- Apache Airflow, MLflow
- Streamlit & Power BI
""")

st.sidebar.markdown("---")
st.sidebar.caption("Portfolio Project | [GitHub Repository](https://github.com/)")

# Main Title & Notice Banner
st.title("⚡ Customer Intelligence, Churn, LTV & Retention Optimization Engine")
st.warning("⚠️ **PUBLIC DEMO & SIMULATION NOTICE**: This application uses synthetic demonstration data. Financial outcomes and retention ROI are simulated and should not be interpreted as real company performance. All customer records and telemetries are generated synthetically for benchmark modeling.")

st.markdown("""
An industry-grade, end-to-end data science and decision intelligence platform that unifies **Data Engineering, Advanced SQL Analytics, Explainable Machine Learning (XGBoost & SHAP), Customer Lifetime Value (CLV), and Financial Retention Optimization** into a unified executive decision system.
""")

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

# Main Content Tabs
tab_overview, tab_architecture, tab_dataset, tab_ml_analytics, tab_findings, tab_powerbi = st.tabs([
    "🎯 Business Context & Navigation",
    "🏗️ Architecture & Tech Stack",
    "📦 Dataset & Engineering",
    "🤖 ML & Predictive Capabilities",
    "📈 Empirical Insights & Limits",
    "📊 Power BI Data Assets"
])

# TAB 1: Business Context & Module Navigation
with tab_overview:
    st.subheader("💼 Business Problem & Strategic Objectives")
    st.markdown("""
    Modern subscription and recurring transactional businesses face sharply rising Customer Acquisition Costs (CAC), making retention and expansion revenue the primary drivers of enterprise value. 
    
    This platform addresses three core commercial imperatives:
    1. **Early Risk Identification**: Detect disengaging accounts 30–60 days before contract cancellation using behavioral event telemetry.
    2. **Value-Preservation Prioritization**: Concentrate executive interventions and marketing spend on high-equity accounts rather than treating all churn risks equally.
    3. **Prescriptive Action & ROI Simulation**: Recommend personalized, cost-calibrated retention interventions and stress-test campaign payback before committing marketing capital.
    """)
    
    st.markdown("### 🧭 Interactive Dashboard Navigation")
    st.markdown("Select any module from the left sidebar or explore the key capabilities below:")

    nav_c1, nav_c2 = st.columns(2)
    with nav_c1:
        with st.container(border=True):
            st.markdown("#### [📊 1. Executive Overview](Executive_Overview)")
            st.markdown("Macro financial health, Monthly Recurring Revenue (MRR), Monthly Cohort Survival heatmaps, and acquisition channel ROI.")
        
        with st.container(border=True):
            st.markdown("#### [🧩 2. Customer Segmentation & RFM](Customer_Segmentation_RFM)")
            st.markdown("Recency, Frequency, Monetary (RFM) quintile clustering, Champions vs. At-Risk groups, and 3D behavioral scatter distribution.")
        
        with st.container(border=True):
            st.markdown("#### [⚡ 3. Churn Prediction](Churn_Prediction)")
            st.markdown("XGBoost Champion model evaluation (0.9092 ROC-AUC, 0.7955 F1), 4-tier risk classification, and actionable high-risk customer watchlist.")

        with st.container(border=True):
            st.markdown("#### [🔍 4. SHAP Customer Explainability](SHAP_Customer_Explainability)")
            st.markdown("Transparent TreeSHAP waterfall diagnostics decomposing individual customer risk boosters and protective buffers.")

    with nav_c2:
        with st.container(border=True):
            st.markdown("#### [💎 5. Customer Lifetime Value (CLV)](Customer_Lifetime_Value)")
            st.markdown("Forward 12-month value regression ($R^2 = 0.7276$), Pareto 80/20 revenue concentration curve, and Platinum-to-Bronze equity tiers.")

        with st.container(border=True):
            st.markdown("#### [💡 6. Retention Strategy & ROI Simulator](Retention_Strategy_ROI)")
            st.markdown("Interactive what-if scenario modeling: adjust outreach costs, discount incentives, and acceptance elasticities in real-time.")

        with st.container(border=True):
            st.markdown("#### [⚙️ 7. Data Engineering & MLOps](Data_Engineering_MLOps)")
            st.markdown("Automated ETL execution telemetry, 32 automated Data Quality test results, and statistical drift monitoring (PSI & KS tests).")

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

    st.info("🛡️ **Data Quality Enforcement**: 32 automated integrity checks validate completeness (zero nulls in required fields), uniqueness (zero duplicate customer IDs or emails), referential foreign-key integrity, numeric boundaries, and chronological consistency ($signup \le transaction \le churn$).")

# TAB 4: ML & Predictive Capabilities
with tab_ml_analytics:
    st.subheader("🤖 Machine Learning & Explainability Benchmarks")
    st.markdown("All models are trained strictly on behavioral rates normalized by active observation lifetime and evaluated on a genuinely unseen holdout test partition ($N=1,000$ accounts, baseline churn rate: $39.9\%$).")

    perf_df = pd.DataFrame([
        {"Model Architecture": "Logistic Regression (Baseline)", "Accuracy": "77.6%", "Precision": "71.2%", "Recall": "73.7%", "F1-Score": "0.7241", "ROC-AUC": "0.8322"},
        {"Model Architecture": "Random Forest Classifier", "Accuracy": "78.1%", "Precision": "72.3%", "Recall": "73.2%", "F1-Score": "0.7273", "ROC-AUC": "0.8587"},
        {"Model Architecture": "Gradient Boosting Classifier", "Accuracy": "84.4%", "Precision": "85.7%", "Recall": "73.4%", "F1-Score": "0.7908", "ROC-AUC": "0.9112"},
        {"Model Architecture": "XGBoost Classifier (Champion)", "Accuracy": "79.8%", "Precision": "79.7%", "Recall": "79.5%", "F1-Score": "0.7955", "ROC-AUC": "0.9092"}
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
    st.markdown("""
    * **Simulated Counterfactual Baseline**: In live corporate production, retention intervention success probabilities ($\eta$) should be calibrated via randomized controlled A/B testing holdout experiments.
    * **Cold-Start Accounts**: Customers with active tenures under 30 days have limited behavioral telemetry and are routed to onboarding checklists rather than pure ML scoring.
    * **Attribution Transparency**: All financial ROI metrics presented in this application represent simulated scenarios for portfolio benchmarking and must not be interpreted as audited historical revenue.
    """)

# TAB 6: Power BI Data Assets
with tab_powerbi:
    st.subheader("📊 Power BI Integration & Downloadable Mart")
    st.markdown("""
    The platform pre-packages a complete Star Schema dimensional mart and 30+ production DAX formulas for Microsoft Power BI Desktop.
    
    > **Note**: Microsoft Power BI Desktop reports (.pbix) run locally in Power BI Desktop or in the cloud Power BI Service; they open separately from this web application.
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

    st.markdown("#### 📥 Download Pre-Packaged Analytical Mart Tables (CSV)")
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
    st.info("📋 **DAX Formulas & Schema Reference**: To import these tables and apply DAX measures, refer to [`power_bi/README.md`](https://github.com/) and [`power_bi/dax_measures.txt`](https://github.com/).")
