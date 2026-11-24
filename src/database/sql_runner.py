"""
SQL Analytics Runner.
Executes analytical SQL scripts, creates views, and fetches analytical DataFrames for dashboards and reports.
"""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy import text
from src.config import SQL_DIR
from src.utils.logger import get_logger
from src.database.connection import db_manager

logger = get_logger("sql_runner")

class SQLAnalyticsRunner:
    """Orchestrates SQL analytics views creation and queries."""

    def __init__(self):
        self.sql_dir = SQL_DIR

    def deploy_all_views(self) -> None:
        """Executes all analytics SQL files to deploy analytical views."""
        script_files = [
            "02_rfm_analysis.sql",
            "03_cohort_retention.sql",
            "04_revenue_trends.sql",
            "05_customer_segmentation.sql",
            "06_acquisition_and_purchase_frequency.sql"
        ]

        logger.info("Deploying analytical SQL views...")
        for script_name in script_files:
            script_path = self.sql_dir / script_name
            if not script_path.exists():
                logger.warning(f"Script {script_name} not found. Skipping.")
                continue

            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()

            statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
            with db_manager.engine.begin() as conn:
                for stmt in statements:
                    try:
                        conn.execute(text(stmt))
                    except Exception as e:
                        logger.error(f"Error executing statement in {script_name}: {e}\nStmt: {stmt[:100]}...")
            logger.info(f"Deployed views from {script_name}")

    def get_rfm_data(self) -> pd.DataFrame:
        """Retrieves RFM segmentation records."""
        query = "SELECT * FROM view_rfm_analysis"
        return db_manager.execute_query(query)

    def get_cohort_matrix(self) -> pd.DataFrame:
        """Retrieves monthly cohort retention matrix."""
        query = "SELECT * FROM view_cohort_retention ORDER BY cohort_month, month_index"
        return db_manager.execute_query(query)

    def get_revenue_trends(self) -> pd.DataFrame:
        """Retrieves monthly revenue trends, ARPU, and MoM growth."""
        query = "SELECT * FROM view_revenue_trends ORDER BY revenue_month ASC"
        return db_manager.execute_query(query)

    def get_customer_segmentation(self) -> pd.DataFrame:
        """Retrieves multi-dimensional customer segmentation table."""
        query = "SELECT * FROM view_customer_segmentation"
        return db_manager.execute_query(query)

    def get_acquisition_metrics(self) -> pd.DataFrame:
        """Retrieves acquisition channels and CAC metrics."""
        query = "SELECT * FROM view_acquisition_metrics ORDER BY acquired_customers DESC"
        return db_manager.execute_query(query)

    def get_purchase_frequency(self) -> pd.DataFrame:
        """Retrieves purchase velocity and average order values by tier."""
        query = "SELECT * FROM view_purchase_frequency ORDER BY avg_spend_per_customer DESC"
        return db_manager.execute_query(query)

if __name__ == "__main__":
    runner = SQLAnalyticsRunner()
    runner.deploy_all_views()
    print("RFM preview:\n", runner.get_rfm_data().head(3))
    print("Cohort preview:\n", runner.get_cohort_matrix().head(3))
