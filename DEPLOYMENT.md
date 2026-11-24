# 🚀 Public Deployment Guide: Streamlit Community Cloud & GitHub

## Customer Intelligence, Churn, LTV & Retention Optimization Engine

This guide provides end-to-end, step-by-step instructions to deploy this project publicly on **GitHub** and **Streamlit Community Cloud**, generating a public HTTPS URL (e.g., `https://customer-intelligence-engine.streamlit.app`) suitable for resumes, LinkedIn profiles, and job applications.

---

## 📋 Table of Contents
1. [Architecture Overview: Public Cloud vs. Local Enterprise](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Pre-Flight Verification](#3-pre-flight-verification)
4. [Step-by-Step GitHub Setup](#4-step-by-step-github-setup)
5. [Step-by-Step Streamlit Community Cloud Deployment](#5-step-by-step-streamlit-community-cloud-deployment)
6. [Secrets & Configuration Management](#6-secrets--configuration-management)
7. [Post-Deployment Verification Checklist](#7-post-deployment-verification-checklist)
8. [Troubleshooting Guide](#8-troubleshooting-guide)

---

## 1. Architecture Overview

This platform uses an environment-aware dual architecture:

| Environment | Database Layer | ML Inference & SHAP | MLOps & Orchestration | Primary Purpose |
|---|---|---|---|---|
| **Streamlit Community Cloud (Public)** | Compact SQLite Demo Mart (`data/customer_intelligence_demo.db`, ~9.8 MB) | Cached In-Memory (`@st.cache_resource`, `@st.cache_data`) | Pre-computed telemetry & audit trail | Fast public demonstration, zero API costs, instant page transitions |
| **Local / Docker (Enterprise)** | PostgreSQL or Local SQLite | Real-time retraining & batch scoring | Apache Airflow DAG & MLflow Tracking Server | Complete engineering pipeline, automated ETL, and model retraining |

---

## 2. Prerequisites

1. **GitHub Account**: [github.com](https://github.com)
2. **Streamlit Community Cloud Account**: [share.streamlit.io](https://share.streamlit.io) (Free; log in using your GitHub account)
3. **Git installed on your machine**: Run `git --version` to verify.

---

## 3. Pre-Flight Verification

Before pushing to GitHub, verify that all necessary deployment artifacts are ready in your project directory:

1. **Cloud Dependencies**: [`requirements.txt`](requirements.txt) includes `streamlit`, `pandas`, `pyarrow`, `scikit-learn`, `xgboost`, `shap`, `plotly`, etc.
2. **Streamlit Config**: [`.streamlit/config.toml`](.streamlit/config.toml) defines the dark enterprise theme and security settings.
3. **Demo Database**: `data/customer_intelligence_demo.db` is present (~9.8 MB, well within GitHub's 50 MB threshold).
4. **Model Artifacts**: `models/churn_xgb_model.joblib`, `models/clv_model.joblib`, `models/churn_metrics.json`, etc. are present.
5. **Entrypoint**: `streamlit_app.py` and `dashboard/app.py` are tested.

Run the automated test suite to ensure 100% compliance:
```bash
python -m pytest tests/ -v
```
*(All 11 tests should pass).*

---

## 4. Step-by-Step GitHub Setup

Open your terminal or command prompt in the project root directory (`customer_churn`):

### Step 4.1: Initialize Git Repository
```bash
# Initialize git if not already initialized
git init

# Verify git status
git status
```

### Step 4.2: Stage and Commit All Project Files
```bash
# Stage all files (.gitignore automatically excludes local logs and raw uncompressed files)
git add .

# Create initial commit
git commit -m "feat: complete recruitment-ready customer intelligence and retention engine"
```

### Step 4.3: Create a New GitHub Repository
1. Go to [github.com/new](https://github.com/new).
2. Repository name: `customer-retention-intelligence-engine` (or your preferred name).
3. Description: `End-to-End Customer Intelligence, Churn, LTV & Retention Optimization Platform with XGBoost, SHAP, Streamlit, and Power BI.`
4. Visibility: **Public** (required for free Streamlit Community Cloud hosting and resume viewing).
5. Do **NOT** initialize with README, .gitignore, or license (these already exist locally).
6. Click **Create repository**.

### Step 4.4: Link Local Repository and Push to GitHub
Copy the commands shown on your new GitHub repo page:
```bash
# Rename branch to main
git branch -M main

# Add remote origin (replace YOUR-USERNAME with your actual GitHub username)
git remote add origin https://github.com/YOUR-USERNAME/customer-retention-intelligence-engine.git

# Push to GitHub
git push -u origin main
```

---

## 5. Step-by-Step Streamlit Community Cloud Deployment

### Step 5.1: Access Streamlit Community Cloud
1. Navigate to [share.streamlit.io](https://share.streamlit.io).
2. Sign in with your **GitHub** account.
3. Click the blue button: **"New app"** (or "Create app").

### Step 5.2: Configure Deployment Settings
Fill out the deployment dialog:
* **Repository**: `YOUR-USERNAME/customer-retention-intelligence-engine`
* **Branch**: `main`
* **Main file path**: `streamlit_app.py` *(or `dashboard/app.py`)*
* **App URL (optional customization)**: Click the dropdown to customize your public subdomain:
  e.g., `https://customer-intelligence-engine.streamlit.app`

### Step 5.3: Deploy the Application
1. Click **"Deploy!"**.
2. Streamlit Cloud will allocate a container, install packages from `requirements.txt`, and boot the app.
3. Within 1 to 2 minutes, your application will be live at your public HTTPS URL!

---

## 6. Secrets & Configuration Management

### For the Default Public Demo:
No secrets or environment variables are needed! The application automatically detects `data/customer_intelligence_demo.db` and launches in high-performance demo mode.

### For Connecting to an External PostgreSQL Database (Optional):
If you wish to point the public app to an external managed PostgreSQL instance (e.g. AWS RDS, Neon, Supabase):
1. In Streamlit Cloud, go to **App Settings** > **Secrets**.
2. Paste your credentials (see template in [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)):
```toml
DB_TYPE = "postgresql"
DB_HOST = "your-database-host.com"
DB_PORT = "5432"
DB_NAME = "customer_intelligence"
DB_USER = "your_user"
DB_PASSWORD = "your_secure_password"
DB_READONLY = "true"
```
3. Save changes. The app will automatically connect to PostgreSQL on the next request.

---

## 7. Post-Deployment Verification Checklist

Once the app is running online, verify all 7 modules:

- [ ] **Landing Page (`/`)**: Pulse KPI cards render; architecture diagram, tabs, and Power BI download buttons are interactive.
- [ ] **1. Executive Overview**: Monthly revenue charts, ARPU metrics, and cohort survival heatmap display cleanly.
- [ ] **2. Customer Segmentation (RFM)**: 3D RFM scatter plot and segment share treemap load; filter controls respond.
- [ ] **3. Churn Prediction**: Algorithm benchmark leaderboard shows XGBoost Champion (0.9092 ROC-AUC); high-risk customer watchlist filtering works.
- [ ] **4. SHAP Customer Explainability**: Select any customer from the dropdown; verify the TreeSHAP waterfall plot renders showing red risk amplifiers and green protective factors.
- [ ] **5. Customer Lifetime Value**: Pareto 80/20 concentration curve and value tier distribution load; filtering works.
- [ ] **6. Retention Strategy & ROI Simulator**: Adjust the Outreach Cost, Discount Concession, and Acceptance Rate sliders; verify the simulated revenue saved and ROI update dynamically.
- [ ] **7. Data Engineering & MLOps**: Ingestion logs, 32 data quality audit results, and statistical drift stability metrics (PSI = 0.067) display properly.

---

## 8. Troubleshooting Guide

### Issue 1: "ModuleNotFoundError: No module named 'pyarrow'"
* **Cause**: `pyarrow` was missing from `requirements.txt`.
* **Fix**: Ensure `pyarrow>=14.0.0` is present in `requirements.txt` and rebuild the app in Streamlit Cloud (**Settings** > **Reboot app**).

### Issue 2: "File size exceeds 100 MB" on `git push`
* **Cause**: The raw uncompressed SQLite file or raw CSVs were staged.
* **Fix**: Ensure `.gitignore` is active. Use `data/customer_intelligence_demo.db` (9.8 MB) instead of un-vacuumed raw tables.

### Issue 3: Streamlit Memory Limit Exceeded (1 GB cap)
* **Cause**: Loading full raw clickstream sessions (570k+ rows) into browser memory.
* **Fix**: The platform uses `@st.cache_data` and pre-aggregated analytical tables/views, keeping peak memory usage under 250 MB.

### Issue 4: Missing Database File on Cloud
* **Cause**: `data/customer_intelligence_demo.db` was not pushed to GitHub.
* **Fix**: Run `git status` to verify `data/customer_intelligence_demo.db` is tracked. If necessary, run:
  ```bash
  git add -f data/customer_intelligence_demo.db
  git commit -m "chore: add demo database artifact"
  git push origin main
  ```

---

## 9. Showcasing on Your Resume & Portfolio

Add this link to your resume and professional profiles:

```text
Projects:
Customer Intelligence, Churn, LTV & Retention Optimization Engine
• Live Demo: https://customer-intelligence-engine.streamlit.app
• Code: https://github.com/YOUR-USERNAME/customer-retention-intelligence-engine
• Built an end-to-end data science and retention optimization platform predicting customer churn (XGBoost, 0.9092 ROC-AUC) and 12-month CLV (Gradient Boosting, R²=0.73) with TreeSHAP waterfall explainability.
• Implemented automated ETL with 32 data quality validation checks in PostgreSQL/SQLite and an interactive what-if financial ROI retention simulator in Streamlit.
```
