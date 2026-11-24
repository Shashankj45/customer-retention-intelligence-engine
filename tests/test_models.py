"""
Tests for Churn ML, Explainability, and CLV Prediction Engines.
"""

import pytest
import joblib
import numpy as np
import pandas as pd
from src.config import MODELS_DIR, PROCESSED_DATA_DIR
from src.models.explainability import ChurnExplainabilityEngine

def test_churn_model_artifacts_exist():
    model_path = MODELS_DIR / "churn_xgb_model.joblib"
    prep_path = MODELS_DIR / "churn_preprocessor.joblib"
    meta_path = MODELS_DIR / "churn_metrics.json"

    assert model_path.exists(), "Trained XGBoost model artifact is missing."
    assert prep_path.exists(), "Feature preprocessor artifact is missing."
    assert meta_path.exists(), "Model evaluation metrics JSON is missing."

def test_clv_model_artifacts_exist():
    clv_path = MODELS_DIR / "clv_model.joblib"
    assert clv_path.exists(), "Trained CLV model artifact is missing."

def test_churn_inference_output_bounds():
    model = joblib.load(MODELS_DIR / "churn_xgb_model.joblib")
    prep = joblib.load(MODELS_DIR / "churn_preprocessor.joblib")
    features_df = pd.read_parquet(PROCESSED_DATA_DIR / "customer_features.parquet")

    numerical_cols = prep.transformers_[0][2]
    categorical_cols = prep.transformers_[1][2]
    sample = features_df.head(10)[numerical_cols + categorical_cols]

    X_trans = prep.transform(sample)
    probs = model.predict_proba(X_trans)[:, 1]

    assert len(probs) == 10
    assert (probs >= 0.0).all() and (probs <= 1.0).all(), "Predicted probabilities must be bounded in [0, 1]"

def test_shap_explanation_structure():
    explainer = ChurnExplainabilityEngine()
    features_df = pd.read_parquet(PROCESSED_DATA_DIR / "customer_features.parquet")
    first_cid = features_df["customer_id"].iloc[0]

    explanation = explainer.explain_customer(first_cid)
    assert explanation["customer_id"] == first_cid
    assert 0.0 <= explanation["churn_probability"] <= 1.0
    assert "top_risk_drivers" in explanation
    assert "protective_factors" in explanation
    assert len(explanation["top_risk_drivers"]) <= 5
