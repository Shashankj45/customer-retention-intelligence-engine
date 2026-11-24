"""
Unit and Integration Tests for Synthetic Data Generator.
"""

import pytest
import pandas as pd
from src.data.generator import CustomerDataGenerator

@pytest.fixture(scope="module")
def sample_datasets():
    generator = CustomerDataGenerator(num_customers=50, seed=99)
    return generator.generate_all()

def test_customers_shape_and_columns(sample_datasets):
    customers = sample_datasets["customers"]
    assert len(customers) == 50
    expected_cols = [
        "customer_id", "customer_name", "email", "country", "age",
        "gender", "signup_date", "subscription_tier", "contract_type",
        "payment_method", "churn_status"
    ]
    for col in expected_cols:
        assert col in customers.columns
    assert customers["customer_id"].is_unique
    assert customers["email"].is_unique

def test_transactions_referential_integrity(sample_datasets):
    customers = sample_datasets["customers"]
    transactions = sample_datasets["transactions"]
    assert len(transactions) > 0
    # Every customer in transactions must exist in customers
    assert transactions["customer_id"].isin(customers["customer_id"]).all()
    assert (transactions["amount"] >= 0).all()

def test_website_sessions_validity(sample_datasets):
    sessions = sample_datasets["website_sessions"]
    assert len(sessions) > 0
    assert (sessions["duration_seconds"] >= 0).all()
    assert (sessions["pages_viewed"] >= 1).all()

def test_support_tickets_csat_range(sample_datasets):
    tickets = sample_datasets["support_tickets"]
    if len(tickets) > 0:
        assert tickets["csat_score"].between(1, 5).all()
        assert (tickets["resolution_time_hours"] >= 0).all()
