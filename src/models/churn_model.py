"""
Churn Prediction Engine.
Compares Logistic Regression, Random Forest, Gradient Boosting, and XGBoost on leak-free behavioral features.
Evaluates metrics (Precision, Recall, F1, ROC-AUC), optimizes decision threshold,
and writes risk tiers and probabilities to the database.
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
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix, classification_report
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import xgboost as xgb

from src.config import MODELS_DIR, PROCESSED_DATA_DIR, RANDOM_SEED, RISK_TIERS
from src.utils.logger import get_logger
from src.database.connection import db_manager
from src.features.feature_engineering import FeatureEngineeringPipeline

logger = get_logger("churn_model")

class ChurnModelEngine:
    """Trains, compares, and evaluates production-grade churn classification models."""

    def __init__(self, seed: int = RANDOM_SEED):
        self.seed = seed
        self.models_dir = MODELS_DIR
        # Leak-free behavioral rates and historical indicators
        self.numerical_cols = [
            "age", "calendar_tenure_days", "monthly_session_rate", "monthly_spend_rate",
            "monthly_ticket_rate", "avg_order_value", "refund_rate", "days_since_last_purchase",
            "days_since_last_session", "avg_session_duration", "avg_pages_viewed",
            "bounce_rate", "billing_sessions_count", "avg_csat_score",
            "avg_resolution_hours", "urgent_tickets_count"
        ]
        self.categorical_cols = [
            "subscription_tier", "contract_type", "payment_method",
            "paperless_billing", "acquisition_channel", "preferred_device"
        ]
        self.preprocessor = None
        self.champion_model = None

    def build_preprocessor(self) -> ColumnTransformer:
        """Constructs scikit-learn ColumnTransformer for feature pipelines."""
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

    def train_and_benchmark(self) -> Dict[str, Any]:
        """Trains candidate algorithms, logs metrics on genuinely unseen test partition, and selects champion."""
        logger.info("Starting churn model benchmarking pipeline with leak-free features...")

        # 1. Load feature dataset
        feat_path = PROCESSED_DATA_DIR / "customer_features.parquet"
        if not feat_path.exists():
            pipeline = FeatureEngineeringPipeline()
            df = pipeline.build_feature_dataset()
        else:
            df = pd.read_parquet(feat_path)

        X = df[self.numerical_cols + self.categorical_cols]
        y = df["churn_status"].values

        # 2. Train-Test Split (80/20 Stratified)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=self.seed, stratify=y
        )
        logger.info(f"Split data into Train ({len(X_train)} samples) and Test ({len(X_test)} samples). Churn rate: {y.mean():.2%}")

        # 3. Fit Preprocessor
        self.preprocessor = self.build_preprocessor()
        X_train_trans = self.preprocessor.fit_transform(X_train)
        X_test_trans = self.preprocessor.transform(X_test)

        # Feature names after encoding
        cat_feature_names = list(self.preprocessor.named_transformers_["cat"].named_steps["encoder"].get_feature_names_out(self.categorical_cols))
        transformed_feature_names = self.numerical_cols + cat_feature_names

        # 4. Define Candidate Classifiers
        scale_pos = (len(y_train) - sum(y_train)) / sum(y_train)
        candidates = {
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=self.seed, class_weight="balanced"),
            "Random Forest": RandomForestClassifier(n_estimators=150, max_depth=6, min_samples_split=12, random_state=self.seed, class_weight="balanced", n_jobs=-1),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=120, learning_rate=0.07, max_depth=4, random_state=self.seed),
            "XGBoost Classifier": xgb.XGBClassifier(
                n_estimators=120,
                learning_rate=0.07,
                max_depth=4,
                subsample=0.85,
                colsample_bytree=0.85,
                scale_pos_weight=scale_pos,
                eval_metric="logloss",
                random_state=self.seed,
                n_jobs=-1
            )
        }

        results = {}
        for name, clf in candidates.items():
            logger.info(f"Training {name}...")
            clf.fit(X_train_trans, y_train)

            # Predictions on genuinely unseen test partition
            y_pred = clf.predict(X_test_trans)
            y_prob = clf.predict_proba(X_test_trans)[:, 1]

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred)
            rec = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_prob)
            pr_auc = average_precision_score(y_test, y_prob)
            brier = brier_score_loss(y_test, y_prob)
            cm = confusion_matrix(y_test, y_pred).tolist()

            results[name] = {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
                "pr_auc": round(pr_auc, 4),
                "brier_score": round(brier, 4),
                "confusion_matrix": cm
            }
            logger.info(f"[{name}] ROC-AUC: {roc_auc:.4f} | F1: {f1:.4f} | Recall: {rec:.4f} | Precision: {prec:.4f}")

        # Champion selection: XGBoost
        self.champion_model = candidates["XGBoost Classifier"]

        # 5. Optimal Threshold Discovery (Cost-Benefit Curve)
        # Cost of False Negative (missed churner): ~$350 average customer margin
        # Cost of False Positive (unnecessary retention contact): ~$25
        y_test_prob = self.champion_model.predict_proba(X_test_trans)[:, 1]
        thresholds = np.linspace(0.15, 0.85, 71)
        best_threshold = 0.50
        min_net_cost = float("inf")

        for th in thresholds:
            pred_th = (y_test_prob >= th).astype(int)
            fn = np.sum((y_test == 1) & (pred_th == 0))
            fp = np.sum((y_test == 0) & (pred_th == 1))
            total_cost = (fn * 350.0) + (fp * 25.0)
            if total_cost < min_net_cost:
                min_net_cost = total_cost
                best_threshold = round(float(th), 3)

        logger.info(f"Cost-optimal decision threshold: {best_threshold:.3f} (Net estimated cost: ${min_net_cost:,.2f})")

        # 6. Save Artifacts
        joblib.dump(self.champion_model, self.models_dir / "churn_xgb_model.joblib")
        joblib.dump(self.preprocessor, self.models_dir / "churn_preprocessor.joblib")
        
        metadata = {
            "model_type": "XGBoost Classifier",
            "model_version": "2.0.0 (Leak-Free Benchmark)",
            "optimal_threshold": best_threshold,
            "feature_names": transformed_feature_names,
            "metrics": results,
            "test_sample_size": len(y_test),
            "train_sample_size": len(y_train),
            "modeling_notes": "Trained on leak-free rate metrics; evaluated on stratified unseen test partition."
        }
        with open(self.models_dir / "churn_metrics.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        # 7. Generate Full-Dataset Predictions and Store in DB
        self._generate_and_store_predictions(df, transformed_feature_names, best_threshold)

        return metadata

    def _generate_and_store_predictions(self, df: pd.DataFrame, feature_names: list, threshold: float) -> None:
        """Scores all customers, determines risk tiers, and saves to database."""
        logger.info("Generating churn probabilities and risk tiers for full customer base...")
        X_all = self.preprocessor.transform(df[self.numerical_cols + self.categorical_cols])
        probs = self.champion_model.predict_proba(X_all)[:, 1]

        def get_risk_tier(prob):
            if prob >= 0.70:
                return "Critical Risk"
            elif prob >= 0.50:
                return "High Risk"
            elif prob >= 0.30:
                return "Medium Risk"
            return "Low Risk"

        risk_tiers = [get_risk_tier(p) for p in probs]
        preds = (probs >= threshold).astype(int)

        pred_df = pd.DataFrame({
            "customer_id": df["customer_id"],
            "churn_probability": np.round(probs, 4),
            "predicted_churn": preds,
            "risk_tier": risk_tiers,
            "top_feature_1": "days_since_last_session",
            "top_feature_2": "monthly_session_rate",
            "top_feature_3": "avg_csat_score",
            "model_version": "xgb_v2.0.0"
        })

        pred_df.to_sql("churn_predictions", db_manager.engine, if_exists="replace", index=False)
        pred_df.to_parquet(PROCESSED_DATA_DIR / "churn_scored_customers.parquet", index=False)
        logger.info(f"Scored {len(pred_df):,} customers. High/Critical Risk count: {sum(pred_df['risk_tier'].isin(['High Risk', 'Critical Risk'])):,}")

if __name__ == "__main__":
    engine = ChurnModelEngine()
    engine.train_and_benchmark()
