"""
Automated ETL Pipeline.
Extracts raw customer, transaction, session, and ticket data.
Cleanses, validates, transforms, and loads into PostgreSQL/SQLite database.
Logs execution metrics and failures to pipeline_execution_logs table.
"""

import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict
import pandas as pd
from sqlalchemy import text
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SQL_DIR
from src.utils.logger import get_logger
from src.database.connection import db_manager
from src.data.generator import CustomerDataGenerator
from src.data.validator import DataQualityValidator

logger = get_logger("etl_pipeline")

class ETLPipeline:
    """End-to-End Enterprise ETL Pipeline with transaction management and execution auditing."""

    def __init__(self):
        self.execution_id = f"ETL-{uuid.uuid4().hex[:8].upper()}"

    def run(self) -> bool:
        """Executes full extraction, transformation, quality validation, and database load."""
        start_time = datetime.now()
        start_ts = time.time()
        logger.info(f"Starting ETL Pipeline run [{self.execution_id}]...")

        try:
            # 1. Initialize DB Schema first so audit & log tables exist
            self._initialize_schema()

            self._log_pipeline_step("pipeline_start", "IN_PROGRESS", 0, start_time)

            # 2. Extract
            datasets = self._extract()

            # 3. Transform & Clean
            cleaned_datasets = self._transform(datasets)

            # 4. Validate Data Quality
            validator = DataQualityValidator(self.execution_id)
            is_valid, audit_records = validator.validate_all(cleaned_datasets)
            validator.save_audit_results()

            if not is_valid:
                logger.warning("Data quality validation reported issues. Review data_quality_audit table.")

            # 5. Load to Database
            self._load(cleaned_datasets)

            # 6. Save Processed Backups
            for name, df in cleaned_datasets.items():
                dest = PROCESSED_DATA_DIR / f"{name}_clean.parquet"
                df.to_parquet(dest, index=False)
                # Also save CSV for simple inspection
                df.to_csv(PROCESSED_DATA_DIR / f"{name}_clean.csv", index=False)

            total_records = sum(len(df) for df in cleaned_datasets.values())
            end_time = datetime.now()
            duration = round(time.time() - start_ts, 2)

            self._log_pipeline_step(
                step_name="pipeline_complete",
                status="SUCCESS",
                records=total_records,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )

            logger.info(f"ETL Pipeline [{self.execution_id}] finished successfully in {duration}s. {total_records:,} total records loaded.")
            return True

        except Exception as e:
            end_time = datetime.now()
            duration = round(time.time() - start_ts, 2)
            error_msg = str(e)
            logger.error(f"ETL Pipeline [{self.execution_id}] failed: {error_msg}", exc_info=True)
            self._log_pipeline_step(
                step_name="pipeline_error",
                status="FAILED",
                records=0,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                error_msg=error_msg
            )
            return False

    def _initialize_schema(self) -> None:
        """Executes DDL statements to ensure all tables exist."""
        ddl_path = SQL_DIR / "01_schema_ddl.sql"
        if not ddl_path.exists():
            raise FileNotFoundError(f"Schema file not found at {ddl_path}")

        logger.info(f"Applying schema definitions from {ddl_path.name}...")
        with open(ddl_path, "r", encoding="utf-8") as f:
            ddl_content = f.read()

        # Split statements by semicolon and execute each
        statements = [stmt.strip() for stmt in ddl_content.split(";") if stmt.strip()]
        with db_manager.engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
        logger.info("Database schema initialized.")

    def _extract(self) -> Dict[str, pd.DataFrame]:
        """Extracts datasets from raw storage or generates if missing."""
        required = ["customers", "transactions", "website_sessions", "support_tickets"]
        data = {}
        missing = [name for name in required if not (RAW_DATA_DIR / f"{name}.csv").exists()]

        if missing:
            logger.info(f"Raw data files missing ({missing}). Running synthetic generator...")
            generator = CustomerDataGenerator()
            data = generator.generate_all()
        else:
            logger.info("Extracting data from raw CSV files...")
            for name in required:
                data[name] = pd.read_csv(RAW_DATA_DIR / f"{name}.csv")

        return data

    def _transform(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Cleans, standardizes datatypes, and trims whitespace."""
        logger.info("Transforming and standardizing datasets...")
        cleaned = {}

        # 1. Customers
        c_df = datasets["customers"].copy()
        for col in c_df.select_dtypes(include="object").columns:
            c_df[col] = c_df[col].astype(str).str.strip()
        c_df["signup_date"] = pd.to_datetime(c_df["signup_date"]).dt.date
        c_df["churn_status"] = c_df["churn_status"].fillna(0).astype(int)
        c_df["paperless_billing"] = c_df["paperless_billing"].fillna(1).astype(int)
        cleaned["customers"] = c_df

        # 2. Transactions
        tx_df = datasets["transactions"].copy()
        for col in tx_df.select_dtypes(include="object").columns:
            tx_df[col] = tx_df[col].astype(str).str.strip()
        tx_df["transaction_date"] = pd.to_datetime(tx_df["transaction_date"])
        tx_df["amount"] = pd.to_numeric(tx_df["amount"], errors="coerce").fillna(0.0)
        cleaned["transactions"] = tx_df

        # 3. Website Sessions
        s_df = datasets["website_sessions"].copy()
        for col in s_df.select_dtypes(include="object").columns:
            s_df[col] = s_df[col].astype(str).str.strip()
        s_df["session_date"] = pd.to_datetime(s_df["session_date"])
        s_df["duration_seconds"] = pd.to_numeric(s_df["duration_seconds"], errors="coerce").fillna(0).astype(int)
        s_df["pages_viewed"] = pd.to_numeric(s_df["pages_viewed"], errors="coerce").fillna(1).astype(int)
        s_df["is_bounced"] = s_df["is_bounced"].fillna(0).astype(int)
        cleaned["website_sessions"] = s_df

        # 4. Support Tickets
        t_df = datasets["support_tickets"].copy()
        for col in t_df.select_dtypes(include="object").columns:
            t_df[col] = t_df[col].astype(str).str.strip()
        t_df["created_date"] = pd.to_datetime(t_df["created_date"])
        t_df["csat_score"] = pd.to_numeric(t_df["csat_score"], errors="coerce").fillna(3).astype(int)
        t_df["resolution_time_hours"] = pd.to_numeric(t_df["resolution_time_hours"], errors="coerce").fillna(24.0)
        cleaned["support_tickets"] = t_df

        return cleaned

    def _load(self, datasets: Dict[str, pd.DataFrame]) -> None:
        """Loads data into the database using bulk insert."""
        logger.info("Loading cleaned datasets to database tables...")
        # Order matters due to foreign keys: customers first, then children
        load_order = ["customers", "transactions", "website_sessions", "support_tickets"]

        for table in load_order:
            df = datasets[table]
            logger.info(f"Loading {len(df):,} records into '{table}'...")
            df.to_sql(table, db_manager.engine, if_exists="replace", index=False)
            logger.info(f"Successfully loaded '{table}'.")

    def _log_pipeline_step(self, step_name: str, status: str, records: int,
                           start_time: datetime, end_time: datetime = None,
                           duration: float = None, error_msg: str = None) -> None:
        """Persists step execution telemetry to pipeline_execution_logs table."""
        log_id = f"LOG-{uuid.uuid4().hex[:10].upper()}"
        sql = """
        INSERT INTO pipeline_execution_logs 
        (execution_id, pipeline_name, step_name, status, records_processed, start_time, end_time, duration_seconds, error_message)
        VALUES (:exec_id, :pipe_name, :step, :status, :records, :start, :end, :duration, :err)
        """
        params = {
            "exec_id": log_id,
            "pipe_name": "Customer_Intelligence_ETL",
            "step": step_name,
            "status": status,
            "records": records,
            "start": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else None,
            "duration": duration,
            "err": error_msg
        }
        try:
            db_manager.execute_statement(sql, params)
        except Exception as e:
            logger.warning(f"Could not write to pipeline_execution_logs: {e}")

if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.run()
