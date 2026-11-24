"""
Customer Lifetime Value (CLV) Prediction & Segmentation Engine.
Predicts forward 12-month customer revenue using Gradient Boosting Regressor on leak-free historical features,
combines with historical realized spend for Total Projected CLV,
segments customers into value tiers (Platinum, Gold, Silver, Bronze),
and performs Pareto 80/20 revenue concentration analysis.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from src.config import MODELS_DIR, PROCESSED_DATA_DIR, RANDOM_SEED
from src.utils.logger import get_logger
from src.database.connection import db_manager

logger = get_logger("clv_model")

class CLVModelEngine:
    """Trains and serves Customer Lifetime Value predictive regression models without target leakage."""

    def __init__(self, seed: int = RANDOM_SEED):
        self.seed = seed
        self.models_dir = MODELS_DIR
        # Historical behavioral and contract features only (no target proxies or future indicators)
        self.numerical_cols = [
            "age", "calendar_tenure_days", "monthly_session_rate", "monthly_spend_rate",
            "monthly_ticket_rate", "avg_order_value", "refund_rate", "days_since_last_purchase",
            "days_since_last_session", "avg_session_duration", "avg_pages_viewed",
            "bounce_rate", "avg_csat_score", "avg_resolution_hours"
        ]
        self.categorical_cols = [
            "subscription_tier", "contract_type", "payment_method",
            "acquisition_channel", "preferred_device"
        ]
        self.preprocessor = None
        self.model = None

    def build_preprocessor(self) -> ColumnTransformer:
        """Constructs preprocessing pipeline for CLV regression features."""
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])
        return ColumnTransformer([
            ("num", num_pipe, self.numerical_cols),
            ("cat", cat_pipe, self.categorical_cols)
        ])

    def train_and_evaluate(self) -> Dict[str, Any]:
        """Fits CLV regression pipeline on future 12-month spend target and evaluates on unseen test partition."""
        logger.info("Starting CLV model training (Predicting Future 12-Month Revenue without leakage)...")
        df = pd.read_parquet(PROCESSED_DATA_DIR / "customer_features.parquet")

        # Target: Forward 12-Month Spend (Y)
        y = df["future_12m_revenue"].values
        X = df[self.numerical_cols + self.categorical_cols]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=self.seed
        )

        self.preprocessor = self.build_preprocessor()
        X_train_trans = self.preprocessor.fit_transform(X_train)
        X_test_trans = self.preprocessor.transform(X_test)

        logger.info(f"Fitting Gradient Boosting Regressor on {len(X_train)} training samples...")
        self.model = GradientBoostingRegressor(
            n_estimators=140,
            learning_rate=0.07,
            max_depth=4,
            random_state=self.seed
        )
        self.model.fit(X_train_trans, y_train)

        # Predict & Evaluate on unseen test partition
        y_pred = np.maximum(0.0, self.model.predict(X_test_trans))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        metrics = {
            "target": "future_12m_revenue",
            "model_architecture": "GradientBoostingRegressor",
            "r2_score": round(r2, 4),
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
            "mean_actual_future_12m": round(float(y_test.mean()), 2),
            "mean_pred_future_12m": round(float(y_pred.mean()), 2),
            "modeling_notes": "Predicts future 12-month forward spend. Target is not leaked into input features."
        }
        logger.info(f"CLV Forward Model Evaluation: R² = {r2:.4f} | RMSE = ${rmse:,.2f} | MAE = ${mae:,.2f}")

        # Save artifacts
        joblib.dump(self.model, self.models_dir / "clv_model.joblib")
        joblib.dump(self.preprocessor, self.models_dir / "clv_preprocessor.joblib")
        with open(self.models_dir / "clv_metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)

        # Score full customer base and segment into value tiers
        self._score_and_segment_all(df)

        return metrics

    def _score_and_segment_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Scores all customers with predicted forward 12M revenue and computes Total Projected CLV."""
        logger.info("Scoring full customer base with predicted future 12M spend...")
        X_all = self.preprocessor.transform(df[self.numerical_cols + self.categorical_cols])
        pred_future_12m = np.maximum(0.0, self.model.predict(X_all))

        # Total Projected CLV = Realized Historical Spend + Predicted Future 12M Spend
        historical_spend = df["total_completed_spend"].values
        total_clv = np.round(historical_spend + pred_future_12m, 2)

        # Value Tier Percentiles based on Total Projected CLV
        p90 = np.percentile(total_clv, 90)
        p70 = np.percentile(total_clv, 70)
        p40 = np.percentile(total_clv, 40)

        def assign_tier(val):
            if val >= p90:
                return "Platinum Tier (Top 10%)"
            elif val >= p70:
                return "Gold Tier (Top 30%)"
            elif val >= p40:
                return "Silver Tier (Mid 30%)"
            return "Bronze Tier (Bottom 40%)"

        clv_tiers = [assign_tier(v) for v in total_clv]

        clv_df = pd.DataFrame({
            "customer_id": df["customer_id"],
            "historical_revenue": np.round(historical_spend, 2),
            "predicted_future_12m_spend": np.round(pred_future_12m, 2),
            "predicted_clv_12m": total_clv,
            "clv_tier": clv_tiers,
            "model_version": "clv_gbr_v2.0.0"
        })

        # Save to DB and processed parquet
        clv_df.to_sql("clv_predictions", db_manager.engine, if_exists="replace", index=False)
        clv_df.to_parquet(PROCESSED_DATA_DIR / "clv_predictions.parquet", index=False)
        logger.info(f"Saved CLV predictions to database. Mean Total Projected CLV: ${total_clv.mean():,.2f}")

        # Compute Pareto distribution
        self._compute_pareto_analysis(clv_df)
        return clv_df

    def _compute_pareto_analysis(self, clv_df: pd.DataFrame) -> None:
        """Computes Pareto 80/20 cumulative revenue distribution curve."""
        sorted_df = clv_df.sort_values(by="predicted_clv_12m", ascending=False).reset_index(drop=True)
        total_rev = sorted_df["predicted_clv_12m"].sum()

        sorted_df["cumulative_clv"] = sorted_df["predicted_clv_12m"].cumsum()
        sorted_df["cumulative_clv_pct"] = np.round((sorted_df["cumulative_clv"] / total_rev) * 100.0, 2)
        sorted_df["cumulative_customer_pct"] = np.round(((sorted_df.index + 1) / len(sorted_df)) * 100.0, 2)

        # Find 80% threshold
        top_80_idx = sorted_df[sorted_df["cumulative_clv_pct"] >= 80.0].index[0]
        pct_cust_for_80_rev = sorted_df.loc[top_80_idx, "cumulative_customer_pct"]

        pareto_summary = {
            "total_projected_clv_pool": round(float(total_rev), 2),
            "pct_customers_generating_80pct_revenue": float(pct_cust_for_80_rev),
            "top_10pct_revenue_share": float(sorted_df.loc[int(len(sorted_df) * 0.10), "cumulative_clv_pct"]),
            "top_20pct_revenue_share": float(sorted_df.loc[int(len(sorted_df) * 0.20), "cumulative_clv_pct"])
        }

        with open(self.models_dir / "pareto_summary.json", "w", encoding="utf-8") as f:
            json.dump(pareto_summary, f, indent=4)
        logger.info(f"Pareto Analysis: Top {pct_cust_for_80_rev:.1f}% of accounts account for 80% of total lifetime value.")

if __name__ == "__main__":
    clv_engine = CLVModelEngine()
    clv_engine.train_and_evaluate()
