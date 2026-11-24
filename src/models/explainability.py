"""
SHAP Explainability Engine.
Generates local and global model explanations using TreeExplainer on XGBoost.
Produces feature importance rankings, risk-factor breakdowns, and individual waterfall data.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import joblib
import shap

from src.config import MODELS_DIR, PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("shap_explainability")

class ChurnExplainabilityEngine:
    """Computes and serves SHAP explanations for churn model predictions."""

    def __init__(self):
        self.models_dir = MODELS_DIR
        self.model = None
        self.preprocessor = None
        self.explainer = None
        self.feature_names = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Loads trained XGBoost champion and fitted preprocessor."""
        model_path = self.models_dir / "churn_xgb_model.joblib"
        prep_path = self.models_dir / "churn_preprocessor.joblib"

        if not model_path.exists() or not prep_path.exists():
            raise FileNotFoundError("Model or Preprocessor artifact missing. Train churn model first.")

        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(prep_path)
        
        # Load feature names
        import json
        with open(self.models_dir / "churn_metrics.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
            self.feature_names = meta["feature_names"]

        # TreeExplainer is fast for tree-based models
        self.explainer = shap.TreeExplainer(self.model)
        logger.info("SHAP TreeExplainer initialized successfully.")

    def compute_global_importance(self, sample_size: int = 500) -> pd.DataFrame:
        """Computes global feature importance based on mean absolute SHAP values."""
        df = pd.read_parquet(PROCESSED_DATA_DIR / "customer_features.parquet")
        numerical_cols = self.preprocessor.transformers_[0][2]
        categorical_cols = self.preprocessor.transformers_[1][2]

        sample_df = df.sample(min(sample_size, len(df)), random_state=42)
        X_trans = self.preprocessor.transform(sample_df[numerical_cols + categorical_cols])

        shap_values = self.explainer.shap_values(X_trans)

        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        imp_df = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs_shap
        }).sort_values(by="mean_abs_shap", ascending=False).reset_index(drop=True)

        # Save for instant dashboard loading
        imp_df.to_parquet(self.models_dir / "shap_global_importance.parquet", index=False)
        logger.info("Saved global SHAP importance rankings.")
        return imp_df

    def explain_customer(self, customer_id: str) -> Dict[str, Any]:
        """Generates detailed local explanation for a specific customer."""
        df = pd.read_parquet(PROCESSED_DATA_DIR / "customer_features.parquet")
        cust_row = df[df["customer_id"] == customer_id]
        if cust_row.empty:
            raise ValueError(f"Customer {customer_id} not found.")

        numerical_cols = self.preprocessor.transformers_[0][2]
        categorical_cols = self.preprocessor.transformers_[1][2]

        X_trans = self.preprocessor.transform(cust_row[numerical_cols + categorical_cols])
        shap_values = self.explainer.shap_values(X_trans)[0]
        base_value = float(self.explainer.expected_value)

        # Build feature breakdown
        contributions = []
        for feat, val, shap_val in zip(self.feature_names, X_trans[0], shap_values):
            contributions.append({
                "feature": feat,
                "feature_value": round(float(val), 3),
                "shap_value": round(float(shap_val), 4),
                "impact": "Increases Risk" if shap_val > 0 else "Reduces Risk"
            })

        contributions_df = pd.DataFrame(contributions)
        
        # Top 5 risk boosters and top 5 risk mitigators
        risk_drivers = contributions_df[contributions_df["shap_value"] > 0].sort_values(by="shap_value", ascending=False).head(5).to_dict(orient="records")
        protective_factors = contributions_df[contributions_df["shap_value"] < 0].sort_values(by="shap_value", ascending=True).head(5).to_dict(orient="records")

        # Predicted probability
        prob = float(self.model.predict_proba(X_trans)[0, 1])

        return {
            "customer_id": customer_id,
            "churn_probability": round(prob, 4),
            "base_value": round(base_value, 4),
            "top_risk_drivers": risk_drivers,
            "protective_factors": protective_factors,
            "all_contributions": contributions
        }

if __name__ == "__main__":
    explainer = ChurnExplainabilityEngine()
    global_imp = explainer.compute_global_importance(200)
    print("Top 5 Global Features:\n", global_imp.head(5))
