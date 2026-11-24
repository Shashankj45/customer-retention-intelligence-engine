"""
Data Quality Validation Engine.
Performs schema, completeness, referential integrity, and business logic validations.
Saves audit metrics to the data_quality_audit database table.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
from src.utils.logger import get_logger
from src.database.connection import db_manager

logger = get_logger("data_validator")

class DataQualityValidator:
    """Enterprise Data Quality validation engine with automated audit trail logging."""

    def __init__(self, execution_id: str = None):
        self.execution_id = execution_id or f"EXEC-{uuid.uuid4().hex[:8].upper()}"
        self.audit_records: List[Dict] = []

    def validate_all(self, datasets: Dict[str, pd.DataFrame]) -> Tuple[bool, List[Dict]]:
        """Executes full test suite across all relational tables."""
        logger.info(f"Starting Data Quality validation run [{self.execution_id}]...")
        self.audit_records.clear()

        customers = datasets["customers"]
        transactions = datasets["transactions"]
        sessions = datasets["website_sessions"]
        tickets = datasets["support_tickets"]

        # 1. Customers checks
        self._check_nulls("customers", customers, ["customer_id", "email", "signup_date", "subscription_tier"])
        self._check_unique("customers", customers, "customer_id")
        self._check_unique("customers", customers, "email")
        self._check_range("customers", customers, "age", min_val=18, max_val=120)
        self._check_categories("customers", customers, "subscription_tier", ["Free", "Bronze", "Silver", "Gold", "Enterprise"])
        self._check_categories("customers", customers, "contract_type", ["Month-to-Month", "One-Year", "Two-Year"])

        # 2. Transactions checks
        self._check_nulls("transactions", transactions, ["transaction_id", "customer_id", "amount", "transaction_date"])
        self._check_unique("transactions", transactions, "transaction_id")
        self._check_range("transactions", transactions, "amount", min_val=0.0)
        self._check_foreign_key("transactions", transactions, "customer_id", customers, "customer_id")

        # 3. Website Sessions checks
        self._check_nulls("website_sessions", sessions, ["session_id", "customer_id", "session_date", "duration_seconds"])
        self._check_unique("website_sessions", sessions, "session_id")
        self._check_range("website_sessions", sessions, "duration_seconds", min_val=0)
        self._check_range("website_sessions", sessions, "pages_viewed", min_val=1)
        self._check_foreign_key("website_sessions", sessions, "customer_id", customers, "customer_id")

        # 4. Support Tickets checks
        self._check_nulls("support_tickets", tickets, ["ticket_id", "customer_id", "created_date", "csat_score"])
        self._check_unique("support_tickets", tickets, "ticket_id")
        self._check_range("support_tickets", tickets, "csat_score", min_val=1, max_val=5)
        self._check_foreign_key("support_tickets", tickets, "customer_id", customers, "customer_id")

        # 5. Chronological checks (Signup date vs Transactions)
        self._check_chronology(customers, transactions)

        all_passed = all(record["status"] == "PASSED" for record in self.audit_records)
        failed_count = sum(1 for r in self.audit_records if r["status"] == "FAILED")

        logger.info(f"Validation complete: {len(self.audit_records)} checks run. Passed: {len(self.audit_records) - failed_count}, Failed: {failed_count}")
        return all_passed, self.audit_records

    def save_audit_results(self) -> None:
        """Persists validation audit log into database table."""
        if not self.audit_records:
            return
        audit_df = pd.DataFrame(self.audit_records)
        try:
            audit_df.to_sql("data_quality_audit", db_manager.engine, if_exists="append", index=False)
            logger.info(f"Saved {len(audit_df)} audit records to database.")
        except Exception as e:
            logger.error(f"Failed to persist audit records to database: {e}")

    def _check_nulls(self, table_name: str, df: pd.DataFrame, columns: List[str]) -> None:
        for col in columns:
            if col in df.columns:
                null_count = int(df[col].isnull().sum())
                passed = null_count == 0
                self._record(
                    table_name=table_name,
                    check_name=f"null_check_{col}",
                    check_type="Completeness",
                    status="PASSED" if passed else "FAILED",
                    failed_count=null_count,
                    details=f"Column '{col}' has {null_count} null values."
                )

    def _check_unique(self, table_name: str, df: pd.DataFrame, column: str) -> None:
        if column in df.columns:
            dupes = int(df.duplicated(subset=[column]).sum())
            passed = dupes == 0
            self._record(
                table_name=table_name,
                check_name=f"unique_check_{column}",
                check_type="Uniqueness",
                status="PASSED" if passed else "FAILED",
                failed_count=dupes,
                details=f"Column '{column}' has {dupes} duplicate entries."
            )

    def _check_range(self, table_name: str, df: pd.DataFrame, column: str, min_val: float = None, max_val: float = None) -> None:
        if column in df.columns:
            cond = pd.Series(True, index=df.index)
            if min_val is not None:
                cond = cond & (df[column] >= min_val)
            if max_val is not None:
                cond = cond & (df[column] <= max_val)
            invalid_count = int((~cond).sum())
            passed = invalid_count == 0
            self._record(
                table_name=table_name,
                check_name=f"range_check_{column}",
                check_type="Range Integrity",
                status="PASSED" if passed else "FAILED",
                failed_count=invalid_count,
                details=f"Column '{column}' expected [{min_val}, {max_val}], found {invalid_count} violating rows."
            )

    def _check_categories(self, table_name: str, df: pd.DataFrame, column: str, allowed: List[str]) -> None:
        if column in df.columns:
            invalid_count = int((~df[column].isin(allowed)).sum())
            passed = invalid_count == 0
            self._record(
                table_name=table_name,
                check_name=f"allowed_values_{column}",
                check_type="Domain Integrity",
                status="PASSED" if passed else "FAILED",
                failed_count=invalid_count,
                details=f"Column '{column}' found {invalid_count} records outside domain {allowed}."
            )

    def _check_foreign_key(self, child_table: str, child_df: pd.DataFrame, child_col: str,
                           parent_df: pd.DataFrame, parent_col: str) -> None:
        orphans = int((~child_df[child_col].isin(parent_df[parent_col])).sum())
        passed = orphans == 0
        self._record(
            table_name=child_table,
            check_name=f"fk_{child_table}_{child_col}_to_{parent_col}",
            check_type="Referential Integrity",
            status="PASSED" if passed else "FAILED",
            failed_count=orphans,
            details=f"Foreign key {child_col} has {orphans} orphaned records."
        )

    def _check_chronology(self, customers: pd.DataFrame, transactions: pd.DataFrame) -> None:
        # Merge signup date and check transaction_date >= signup_date
        cust_sub = customers[["customer_id", "signup_date"]].copy()
        tx_sub = transactions[["transaction_id", "customer_id", "transaction_date"]].copy()
        merged = tx_sub.merge(cust_sub, on="customer_id", how="left")
        merged["tx_dt"] = pd.to_datetime(merged["transaction_date"]).dt.date
        merged["signup_dt"] = pd.to_datetime(merged["signup_date"]).dt.date
        anachronisms = int((merged["tx_dt"] < merged["signup_dt"]).sum())
        passed = anachronisms == 0
        self._record(
            table_name="transactions",
            check_name="chronological_validity_tx_vs_signup",
            check_type="Business Logic",
            status="PASSED" if passed else "FAILED",
            failed_count=anachronisms,
            details=f"Found {anachronisms} transactions occurring prior to customer signup."
        )

    def _record(self, table_name: str, check_name: str, check_type: str, status: str, failed_count: int, details: str) -> None:
        self.audit_records.append({
            "audit_id": f"AUD-{uuid.uuid4().hex[:10].upper()}",
            "execution_id": self.execution_id,
            "table_name": table_name,
            "check_name": check_name,
            "check_type": check_type,
            "status": status,
            "failed_records_count": failed_count,
            "check_details": details,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
