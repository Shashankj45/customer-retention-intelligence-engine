"""
Configuration module for the Customer Intelligence Platform.
Centralizes paths, database connections, model hyperparameters, and business thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
POWER_BI_DIR = DATA_DIR / "power_bi_exports"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
SQL_DIR = BASE_DIR / "sql"
MLRUNS_DIR = BASE_DIR / "mlruns"

# Ensure all directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, POWER_BI_DIR, MODELS_DIR, LOGS_DIR, SQL_DIR, MLRUNS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "customer_intelligence")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_READONLY = os.getenv("DB_READONLY", "false").lower() in ("true", "1", "yes")

# SQLite Database Resolution (supports standard production and compact cloud demo database)
STANDARD_SQLITE_PATH = DATA_DIR / "customer_intelligence.db"
DEMO_SQLITE_PATH = DATA_DIR / "customer_intelligence_demo.db"

_env_sqlite = os.getenv("SQLITE_PATH")
if _env_sqlite:
    SQLITE_PATH = Path(_env_sqlite)
elif DEMO_SQLITE_PATH.exists() and not STANDARD_SQLITE_PATH.exists():
    SQLITE_PATH = DEMO_SQLITE_PATH
else:
    SQLITE_PATH = STANDARD_SQLITE_PATH

def get_database_url() -> str:
    """Returns database connection URI based on configuration and availability."""
    if DB_TYPE == "postgresql":
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # If standard path missing, check demo path
    active_path = SQLITE_PATH
    if not active_path.exists() and DEMO_SQLITE_PATH.exists():
        active_path = DEMO_SQLITE_PATH
        
    return f"sqlite:///{active_path.as_posix()}"

def is_database_available() -> bool:
    """Checks if the configured database source is accessible."""
    if DB_TYPE == "postgresql":
        try:
            from sqlalchemy import create_engine, text
            test_eng = create_engine(get_database_url(), connect_args={"connect_timeout": 2})
            with test_eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    return SQLITE_PATH.exists() or DEMO_SQLITE_PATH.exists()

# MLflow Configuration
MLFLOW_DB_PATH = DATA_DIR / "mlflow.db"
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{MLFLOW_DB_PATH.as_posix()}")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "customer_churn_intelligence")

# Seed & Sizing
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
DEFAULT_NUM_CUSTOMERS = int(os.getenv("NUM_CUSTOMERS", "5000"))

# Business Constants & ROI Simulation defaults
RETENTION_COST_PER_CONTACT = 25.0       # $25 cost to reach out with retention campaign
DISCOUNT_OFFER_PERCENT = 0.15           # 15% discount offer
AVG_CAMPAIGN_ACCEPTANCE_RATE = 0.45     # 45% of contacted at-risk customers accept and stay
CHURN_PROBABILITY_THRESHOLD = 0.50      # Default decision boundary

# RFM Scoring Quintiles
RFM_SCORE_QUINTILES = 5

# Risk Tiers
RISK_TIERS = {
    "Low Risk": (0.00, 0.30),
    "Medium Risk": (0.30, 0.60),
    "High Risk": (0.60, 0.80),
    "Critical Risk": (0.80, 1.00)
}
