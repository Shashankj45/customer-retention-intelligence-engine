"""
Unit and Integration Tests for ETL Pipeline and Data Quality Validator.
"""

import pytest
import pandas as pd
from src.database.connection import db_manager
from src.data.validator import DataQualityValidator

def test_database_connection():
    df = db_manager.execute_query("SELECT 1 AS test_val")
    assert not df.empty
    assert df["test_val"][0] == 1

def test_data_quality_validator_passes_on_valid_data():
    customers_df = pd.DataFrame({
        "customer_id": ["CUST-001", "CUST-002"],
        "email": ["a@example.com", "b@example.com"],
        "age": [25, 45],
        "signup_date": ["2026-01-01", "2026-02-01"],
        "subscription_tier": ["Gold", "Silver"],
        "contract_type": ["One-Year", "Month-to-Month"]
    })
    transactions_df = pd.DataFrame({
        "transaction_id": ["TXN-001"],
        "customer_id": ["CUST-001"],
        "transaction_date": ["2026-01-15 10:00:00"],
        "amount": [120.50]
    })
    sessions_df = pd.DataFrame({
        "session_id": ["SESS-001"],
        "customer_id": ["CUST-001"],
        "session_date": ["2026-01-10 10:00:00"],
        "duration_seconds": [300],
        "pages_viewed": [4]
    })
    tickets_df = pd.DataFrame({
        "ticket_id": ["TCK-001"],
        "customer_id": ["CUST-001"],
        "created_date": ["2026-01-12 10:00:00"],
        "csat_score": [5]
    })

    datasets = {
        "customers": customers_df,
        "transactions": transactions_df,
        "website_sessions": sessions_df,
        "support_tickets": tickets_df
    }

    validator = DataQualityValidator(execution_id="TEST-EXEC")
    passed, audit_records = validator.validate_all(datasets)
    assert passed is True
    assert all(r["status"] == "PASSED" for r in audit_records)
