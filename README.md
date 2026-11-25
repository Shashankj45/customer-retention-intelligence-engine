# ⚡ Customer Intelligence, Churn, LTV & Retention Optimization Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://customer-retention-intelligence-engine-8rxl25roozqfarvt3vxcch.streamlit.app/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-PostgreSQL%20%7C%20SQLite-336791.svg)](https://www.postgresql.org/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--learn%20%7C%20XGBoost%20%7C%20SHAP-orange.svg)](https://xgboost.readthedocs.io/)
[![Orchestration](https://img.shields.io/badge/orchestration-Apache%20Airflow-017CEE.svg)](https://airflow.apache.org/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow-0194E2.svg)](https://mlflow.org/)
[![Dashboard](https://img.shields.io/badge/dashboard-Streamlit%20%7C%20Power%20BI-FF4B4B.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, end-to-end data science, data engineering, and retention optimization platform. This project ingests multi-source customer telemetry, executes automated ETL with data quality testing, performs advanced SQL analytics (RFM and cohort retention), trains champion XGBoost churn models with SHAP explainability, forecasts Customer Lifetime Value (CLV) with Pareto 80/20 analysis, and simulates marketing campaign ROI.

> **🌐 Live Cloud Demo**: [`https://customer-retention-intelligence-engine-8rxl25roozqfarvt3vxcch.streamlit.app/`](https://customer-retention-intelligence-engine-8rxl25roozqfarvt3vxcch.streamlit.app/)  
> **📖 Step-by-Step Deployment Guide**: See [`DEPLOYMENT.md`](DEPLOYMENT.md) for GitHub and Streamlit Community Cloud setup instructions.  
> **Zero Generative AI or Paid APIs**: Built entirely with free, open-source data science, engineering, and machine learning technologies.
>
> **⚠️ Data Realism & Simulation Governance**:
> - **Synthetic Dataset**: Customer records and telemetries are synthetically generated for benchmark evaluation (5,000 customers, 51,653 transactions, 572,806 sessions, 3,691 tickets — 633,150 total records).
> - **Leak-Free ML**: Feature engineering normalizes behavioral counts into rates by active tenure, eliminating calendar duration leakage (Holdout XGBoost ROC-AUC: 0.9092, F1: 0.7955; CLV Holdout R²: 0.7276).
> - **Simulated ROI**: Retention campaign financial savings reflect what-if scenario simulations based on explicit sensitivity and elasticity parameters, not audited accounting.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Data_Engineering["1. Data Engineering & Ingestion Layer"]
        A1[Customer Demographics] --> B[Automated ETL Pipeline]
        A2[Transactions Ledger] --> B
        A3[Web Telemetry Sessions] --> B
        A4[Support Ticket Inquiries] --> B
        B --> C[Data Quality Validation Suite]
        C --> D[(PostgreSQL / SQLite Database)]
        C -.-> C1[data_quality_audit Table]
        B -.-> B1[pipeline_execution_logs Table]
    end

    subgraph SQL_Analytics["2. Advanced SQL Analytics Layer"]
        D --> E1[RFM Segmentation Engine]
        D --> E2[Monthly Cohort Retention Matrix]
        D --> E3[Revenue Velocity & MRR Trends]
        D --> E4[Acquisition & Purchase Frequency]
    end

    subgraph Machine_Learning["3. Machine Learning & Interpretability"]
        D --> F[Feature Engineering Pipeline]
        F --> G1[Model Benchmark Suite<br>Logistic Reg | RF | GBDT | XGBoost]
        G1 --> G2[XGBoost Champion Model]
        G2 --> G3[Cost-Benefit Threshold Optimizer]
        G2 --> G4[SHAP TreeExplainer<br>Global & Individual Force Decomposition]
        F --> H1[CLV Regression Model<br>Gradient Boosting Regressor]
        H1 --> H2[Pareto 80/20 Concentration Engine]
    end

    subgraph Retention_Optimization["4. Prescriptive Retention Optimization"]
        G2 --> I[Rule-Based Decision Engine]
        H1 --> I
        G4 --> I
        I --> J1[Prioritized Customer Action Roster]
        I --> J2[Interactive What-If ROI Simulator]
    end

    subgraph MLOps_Governance["5. MLOps & Orchestration Layer"]
        K1[Apache Airflow DAG] --> B
        K1 --> G1
        G1 --> K2[MLflow Tracking Registry]
        F --> K3[Statistical Data Drift Monitor<br>PSI & Kolmogorov-Smirnov Tests]
    end

    subgraph Reporting_Presentation["6. Analytics & User Interface Layer"]
        J1 --> L1[Multi-Page Streamlit Enterprise App]
        J2 --> L1
        E1 --> L1
        D --> L2[Power BI Star Schema Analytical Mart<br>CSV / Parquet Exports + DAX Measures]
    end
```

---

## 🚀 Key Modules & Capabilities

### 1. Data Engineering & Storage
- **Interconnected Relational Schema**: Models customers, transactions, website sessions, and customer support tickets with foreign-key constraints and indexes.
- **Dual Database Architecture**: Direct PostgreSQL integration for enterprise production and Docker, with transparent SQLite local fallback for zero-configuration development.
- **Automated Ingestion & ETL**: Cleanses raw telemetry, standardizes datatypes, normalizes timestamps, and builds audit trails in `pipeline_execution_logs`.
- **Data Quality Engine**: Runs automated tests covering completeness (null checks), uniqueness, referential foreign-key integrity, numeric ranges, and chronological consistency.

### 2. Advanced SQL Analytics
- **RFM Segmentation Engine**: Calculates Recency (days inactive), Frequency (completed orders), and Monetary (spend), maps $5 \times 5 \times 5$ quintiles, and categorizes customers into segments (e.g. *Champions*, *Loyal Customers*, *At Risk*, *Can't Lose Them*, *Hibernating*).
- **Monthly Cohort Retention Analysis**: Tracks customer survival across monthly acquisition cohorts for 12 months post-signup.
- **Revenue Trends & MoM Growth**: Computes Gross Revenue, Refund Rates, Net Revenue, ARPU (Average Revenue Per User), and Month-over-Month growth rates.
- **Acquisition & Unit Economics**: Analyzes customer acquisition volume, churn rate, estimated CAC, and LTV/CAC ratios by acquisition channel.

### 3. Machine Learning Churn Prediction & SHAP
- **Leak-Free Relational Feature Engineering**: Formulates all behavioral counts into rates normalized by active observation months (`monthly_session_rate`, `monthly_spend_rate`, `monthly_ticket_rate`), eliminating tenure truncation leakage.
- **Multi-Algorithm Benchmark**: Evaluates Logistic Regression, Random Forest, Gradient Boosting, and XGBoost on a genuinely unseen holdout test split ($N=1,000$).
- **Champion XGBoost Classifier**: Achieves **0.9092 ROC-AUC**, **0.7955 F1-Score**, and **79.5% Recall** on unseen holdout test accounts.
- **Cost-Optimal Threshold Tuning**: Evaluates cost matrix balancing intervention cost (\$25) against lost customer CLV (\$350), selecting an optimal threshold of **0.170**.
- **TreeSHAP Explainability**:
  - Global feature importance: identifies `days_since_last_session`, `monthly_ticket_rate`, `billing_sessions_count`, `avg_csat_score`, and `urgent_tickets_count` as top drivers.
  - Local individual waterfall breakdowns separating positive risk amplifiers from negative protective buffers.

### 4. Customer Lifetime Value (CLV) & Pareto 80/20
- **Segregated 12-Month Forward Value Regression**: Gradient Boosting Regressor forecasts expected 12-month future value ($Y$) using only historical behavioral rates ($X$), completely avoiding target leakage ($R^2 = 0.7276$, $\text{MAE} = \$645.22$).
- **Total Projected CLV Definition**: $\text{Total CLV} = \text{Realized Historical Spend} + \widehat{\text{Future 12M Revenue}}$ (Mean: \$2,640.45).
- **Value Tier Segmentation**: Classifies customer base into *Platinum Tier (Top 10%)*, *Gold Tier (Next 20%)*, *Silver Tier (Next 30%)*, and *Bronze Tier (Bottom 40%)*.
- **Pareto Concentration Engine**: Confirms that the top 20.6% of accounts generate 80.0% of total customer equity.

### 5. Prescriptive Retention & Interactive ROI Simulator
- **Rule-Based Decision Logic**: Synthesizes Churn Risk, CLV Tier, and Root Causes to prescribe personalized interventions (e.g. VIP Concierge Outreach, 20% Annual Contract Commitment Incentive, Priority Support SLA Escalation).
- **Expected Financial Benefit**: Calculates expected revenue saved:
  $$\text{Expected Saved Revenue} = P(\text{Churn}) \times \text{Predicted CLV}_{12m} \times \text{Campaign Success Rate}$$
- **Simulated What-If Scenario Modeling**: Adjusts contact cost, discount incentive, and acceptance rates in real time with dynamic financial waterfall charts (Baseline simulation yields \$548k net benefit, 356.5% ROI across 1,939 targeted high-risk accounts).

### 6. Power BI Integration Package
- **Star Schema Dimensional Mart**: Structured Fact and Dimension tables (`Fact_Transactions`, `Fact_WebsiteSessions`, `Fact_SupportTickets`, `Dim_Customer`, `Dim_Date`, `Dim_ChurnPredictions`, `Dim_CLVPredictions`, `Dim_RFMSegments`, `Dim_RetentionRecommendations`).
- **DAX Measures Repository**: 30+ production DAX formulas for instant Power BI reporting.
- **Automated Exporter**: Pre-generates ready-to-import CSVs and Parquet files into `data/power_bi_exports/`.

### 7. MLOps & Production Governance
- **MLflow Tracking Server**: Logs hyperparameters, evaluation metrics, confusion matrices, and serialized model binaries.
- **Statistical Drift Monitor**: Evaluates Population Stability Index (PSI) and Kolmogorov-Smirnov test statistics to detect distribution shift prior to model degradation.
- **Apache Airflow Orchestration**: End-to-end DAG (`customer_intelligence_retention_pipeline`) orchestrating daily batch ingestion, validation, training, and export.

---

## 📂 Project Directory Structure

```
customer_churn/
├── README.md                               # Project documentation & architecture
├── requirements.txt                        # Core Python dependencies
├── .env.example                            # Configuration template
├── run_pipeline.py                         # Master CLI orchestrator
├── Dockerfile                              # Multi-stage production container
├── docker-compose.yml                      # Postgres, App, MLflow orchestration
├── airflow/
│   └── dags/
│       └── customer_intelligence_dag.py   # Daily Airflow batch DAG
├── sql/
│   ├── 01_schema_ddl.sql                   # Relational DDL & table constraints
│   ├── 02_rfm_analysis.sql                 # RFM scoring & segmentation view
│   ├── 03_cohort_retention.sql             # Monthly cohort survival view
│   ├── 04_revenue_trends.sql               # MRR, ARPU & MoM growth view
│   ├── 05_customer_segmentation.sql        # Behavioral clusters view
│   └── 06_acquisition_and_purchase_frequency.sql # Acquisition & CAC view
├── src/
│   ├── config.py                           # Central configuration & paths
│   ├── data/
│   │   ├── generator.py                    # Interconnected synthetic generator
│   │   ├── etl_pipeline.py                 # Automated ETL & logging pipeline
│   │   └── validator.py                    # Data Quality validation engine
│   ├── database/
│   │   ├── connection.py                   # Postgres / SQLite connection manager
│   │   └── sql_runner.py                   # View deployer & analytical queries
│   ├── features/
│   │   └── feature_engineering.py          # Behavioral feature extraction
│   ├── models/
│   │   ├── churn_model.py                  # XGBoost & algorithm benchmarking
│   │   ├── clv_model.py                    # CLV regression & Pareto analysis
│   │   └── explainability.py               # SHAP TreeExplainer explanations
│   ├── retention/
│   │   ├── decision_engine.py              # Rule-based retention logic
│   │   └── roi_simulator.py                # Financial ROI scenario simulator
│   ├── mlops/
│   │   ├── mlflow_tracker.py               # MLflow experiment tracking
│   │   └── drift_monitor.py                # Statistical data drift (PSI / KS)
│   └── utils/
│       └── logger.py                       # Structured enterprise logging
├── dashboard/
│   ├── app.py                              # Streamlit multi-page entrypoint
│   ├── style.css                           # Modern dashboard CSS styling
│   └── pages/
│       ├── 1_Executive_Overview.py         # Financial KPIs & Cohort heatmap
│       ├── 2_Customer_Segmentation_RFM.py  # 3D RFM scatter & treemaps
│       ├── 3_Churn_Prediction.py           # XGBoost evaluation & Watchlist
│       ├── 4_SHAP_Customer_Explainability.py # Customer diagnostic deep-dive
│       ├── 5_Customer_Lifetime_Value.py    # CLV tiers & Pareto 80/20
│       ├── 6_Retention_Strategy_ROI.py     # Strategy catalog & Simulator
│       └── 7_Data_Engineering_MLOps.py     # Pipeline telemetry & drift
├── power_bi/
│   ├── README.md                           # Power BI setup & visual guide
│   ├── data_model_star_schema.md           # Star Schema specification & ERD
│   ├── dax_measures.txt                    # 30+ Production DAX formulas
│   └── export_data.py                      # Dimensional table exporter
├── tests/
│   ├── test_data_generator.py              # Generator integrity tests
│   ├── test_etl_pipeline.py                # ETL & schema validation tests
│   ├── test_models.py                      # Model inference & SHAP tests
│   └── test_retention.py                   # ROI simulator math tests
├── data/                                   # Data storage (gitignored)
├── models/                                 # Serialized model binaries (.joblib)
└── logs/                                   # Application execution logs
```

---

## 🛠️ Step-by-Step Local Setup Guide

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone <repository_url>
cd customer_churn

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy template configuration
cp .env.example .env
```

*Note: By default, the application runs on local SQLite without needing a running PostgreSQL server. To use PostgreSQL, set `DB_TYPE=postgresql` in `.env`.*

### 3. Execute the Full Pipeline via CLI

Run all pipeline stages in sequence with a single command:

```bash
python run_pipeline.py --step all
```

Or execute individual stages modularly:

```bash
python run_pipeline.py --step generate     # Generate synthetic raw datasets
python run_pipeline.py --step etl          # Run ETL and Data Quality audit
python run_pipeline.py --step sql          # Deploy SQL analytical views
python run_pipeline.py --step churn        # Train churn models & SHAP
python run_pipeline.py --step clv          # Train CLV model & Pareto 80/20
python run_pipeline.py --step retention    # Generate retention recommendations
python run_pipeline.py --step powerbi      # Export Power BI analytical mart
```

### 4. Run Automated Test Suite

```bash
python -m pytest tests/ -v
```

### 5. Launch Interactive Streamlit Dashboard

```bash
# Option A: Modern multi-page entrypoint
streamlit run streamlit_app.py

# Option B: Traditional directory entrypoint
streamlit run dashboard/app.py
```

Open your browser to `http://localhost:8501`.

---

## 🌐 Public Cloud Deployment (GitHub + Streamlit Cloud)

To deploy this application publicly with a free HTTPS URL:

1. Follow the step-by-step setup in [`DEPLOYMENT.md`](DEPLOYMENT.md).
2. Push the codebase to your public GitHub repository (`git push -u origin main`).
3. Connect your GitHub repository on [share.streamlit.io](https://share.streamlit.io).
4. Set **Main file path** to `streamlit_app.py` (or `dashboard/app.py`) and click **Deploy**.
5. Your public web application is live in under 2 minutes!

---

## 🐳 Docker Deployment Guide

To spin up the complete containerized stack (PostgreSQL 15, Streamlit Dashboard, and MLflow Server):

```bash
# Build and start all services
docker-compose up --build -d

# View service logs
docker-compose logs -f app
```

- **Streamlit Dashboard**: `http://localhost:8501`
- **MLflow Tracking UI**: `http://localhost:5000`
- **PostgreSQL Database**: `localhost:5432`

---

## 📊 Business Impact & ROI Summary (Simulated Benchmark)

Across the baseline evaluation cohort of 5,000 customers:
- **Baseline Churn Rate**: ~34.1%
- **Identified Critical & High-Risk Accounts**: 1,939 accounts
- **Estimated Retained Accounts**: 706 accounts
- **Gross Potential Revenue Saved**: **\$701,825.87**
- **Campaign Outreach & Discount Investment**: **\$153,748.88**
- **Simulated Net Economic Benefit**: **+\$548,076.99 (356.5% ROI)**
- **Capital Payback Period**: **2.6 Months**

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
