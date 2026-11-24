"""
Power BI Analytical Mart Data Exporter.
Extracts fact and dimension tables, structures date keys, and outputs clean CSV/Parquet files
ready for 1-click import into Microsoft Power BI Desktop.
"""

from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.config import POWER_BI_DIR, PROCESSED_DATA_DIR
from src.utils.logger import get_logger
from src.database.connection import db_manager
from src.database.sql_runner import SQLAnalyticsRunner

logger = get_logger("power_bi_exporter")

class PowerBIExporter:
    """Exports structured Star Schema tables for Power BI reporting."""

    def __init__(self):
        self.export_dir = POWER_BI_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_all(self) -> None:
        """Generates all 9 Star Schema dimensional and fact tables."""
        logger.info(f"Starting Power BI dimensional data mart export to {self.export_dir}...")

        # 1. Dim_Date
        dim_date = self._generate_dim_date()
        self._save_table("Dim_Date", dim_date)

        # 2. Dim_Customer
        customers = db_manager.execute_query("SELECT * FROM customers")
        customers["signup_date_key"] = pd.to_datetime(customers["signup_date"]).dt.strftime("%Y%m%d").astype(int)
        self._save_table("Dim_Customer", customers)

        # 3. Fact_Transactions
        tx = db_manager.execute_query("SELECT * FROM transactions")
        tx["date_key"] = pd.to_datetime(tx["transaction_date"]).dt.strftime("%Y%m%d").astype(int)
        self._save_table("Fact_Transactions", tx)

        # 4. Fact_WebsiteSessions
        sessions = db_manager.execute_query("SELECT * FROM website_sessions")
        sessions["date_key"] = pd.to_datetime(sessions["session_date"]).dt.strftime("%Y%m%d").astype(int)
        self._save_table("Fact_WebsiteSessions", sessions)

        # 5. Fact_SupportTickets
        tickets = db_manager.execute_query("SELECT * FROM support_tickets")
        tickets["date_key"] = pd.to_datetime(tickets["created_date"]).dt.strftime("%Y%m%d").astype(int)
        self._save_table("Fact_SupportTickets", tickets)

        # 6. Dim_ChurnPredictions
        churn_preds = db_manager.execute_query("SELECT * FROM churn_predictions")
        self._save_table("Dim_ChurnPredictions", churn_preds)

        # 7. Dim_CLVPredictions
        clv_preds = db_manager.execute_query("SELECT * FROM clv_predictions")
        self._save_table("Dim_CLVPredictions", clv_preds)

        # 8. Dim_RFMSegments
        runner = SQLAnalyticsRunner()
        rfm_df = runner.get_rfm_data()
        self._save_table("Dim_RFMSegments", rfm_df)

        # 9. Dim_RetentionRecommendations
        rec_df = db_manager.execute_query("SELECT * FROM retention_recommendations")
        self._save_table("Dim_RetentionRecommendations", rec_df)

        logger.info("Power BI analytical export completed successfully.")

    def _generate_dim_date(self) -> pd.DataFrame:
        """Generates calendar dimension table spanning 3 full years."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2027, 1, 1)
        date_range = pd.date_range(start_date, end_date, freq="D")

        dates = []
        for d in date_range:
            dates.append({
                "date_key": int(d.strftime("%Y%m%d")),
                "full_date": d.strftime("%Y-%m-%d"),
                "year": d.year,
                "quarter": f"Q{((d.month - 1) // 3) + 1}",
                "month_num": d.month,
                "month_name": d.strftime("%B"),
                "year_month": d.strftime("%Y-%m"),
                "day_of_month": d.day,
                "day_of_week": d.strftime("%A"),
                "is_weekend": 1 if d.weekday() >= 5 else 0
            })
        return pd.DataFrame(dates)

    def _save_table(self, name: str, df: pd.DataFrame) -> None:
        """Saves both CSV and Parquet formats."""
        csv_path = self.export_dir / f"{name}.csv"
        parquet_path = self.export_dir / f"{name}.parquet"
        df.to_csv(csv_path, index=False)
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Exported {name} ({len(df):,} rows) -> {csv_path.name}")

if __name__ == "__main__":
    exporter = PowerBIExporter()
    exporter.export_all()
