"""
Streamlit Cloud & Public Web Entrypoint.
Customer Intelligence, Churn, LTV & Retention Optimization Engine.

Supports both:
1. Direct root launch: `streamlit run streamlit_app.py` (Modern Streamlit Multi-Page Navigation)
2. Module path launch: `streamlit run dashboard/app.py` (Traditional Streamlit Directory Pages)
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

# Configure multi-page navigation across all modules
home_page = st.Page("dashboard/app.py", title="Platform Overview & Notice", icon="⚡", default=True)
page_1 = st.Page("dashboard/pages/1_Executive_Overview.py", title="1. Executive Overview", icon="📊")
page_2 = st.Page("dashboard/pages/2_Customer_Segmentation_RFM.py", title="2. Customer Segmentation (RFM)", icon="🧩")
page_3 = st.Page("dashboard/pages/3_Churn_Prediction.py", title="3. Churn Prediction (XGBoost)", icon="⚡")
page_4 = st.Page("dashboard/pages/4_SHAP_Customer_Explainability.py", title="4. SHAP Explainability", icon="🔍")
page_5 = st.Page("dashboard/pages/5_Customer_Lifetime_Value.py", title="5. Customer Lifetime Value", icon="💎")
page_6 = st.Page("dashboard/pages/6_Retention_Strategy_ROI.py", title="6. Retention Strategy & ROI", icon="💡")
page_7 = st.Page("dashboard/pages/7_Data_Engineering_MLOps.py", title="7. Data Engineering & MLOps", icon="⚙️")

pg = st.navigation({
    "Platform Home": [home_page],
    "Analytics & ML Modules": [page_1, page_2, page_3, page_4, page_5, page_6],
    "Infrastructure & Governance": [page_7]
})

pg.run()
