"""
MLflow Experiment Tracking and Model Registry Engine.
Logs hyperparameters, multi-metric evaluations, confusion matrices, and artifacts for churn and CLV pipelines.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import mlflow.xgboost

from src.config import MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME, MODELS_DIR
from src.utils.logger import get_logger

logger = get_logger("mlflow_tracker")

class MLflowTracker:
    """Manages MLflow experiment logging, metric tracking, and artifact registry."""

    def __init__(self):
        # Silence agent hint log and set local tracking
        os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
        self.tracking_uri = MLFLOW_TRACKING_URI
        self.experiment_name = MLFLOW_EXPERIMENT_NAME
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)
        logger.info(f"Initialized MLflow Tracker at {self.tracking_uri} for experiment '{self.experiment_name}'")

    def log_churn_experiment(self) -> str:
        """Logs the benchmarked churn models and champion XGBoost run to MLflow."""
        meta_path = MODELS_DIR / "churn_metrics.json"
        if not meta_path.exists():
            raise FileNotFoundError("Churn metrics artifact missing.")

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        xgb_metrics = metadata["metrics"]["XGBoost Classifier"]
        run_name = f"XGBoost_Churn_Champion_v{metadata['model_version']}"

        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id
            logger.info(f"Logging MLflow run {run_id} ({run_name})...")

            # Log Hyperparameters
            mlflow.log_params({
                "model_type": metadata["model_type"],
                "model_version": metadata["model_version"],
                "optimal_threshold": metadata["optimal_threshold"],
                "train_sample_size": metadata["train_sample_size"],
                "test_sample_size": metadata["test_sample_size"],
                "n_estimators": 150,
                "learning_rate": 0.06,
                "max_depth": 5,
                "subsample": 0.85,
                "colsample_bytree": 0.85
            })

            # Log Evaluation Metrics
            mlflow.log_metrics({
                "accuracy": xgb_metrics["accuracy"],
                "precision": xgb_metrics["precision"],
                "recall": xgb_metrics["recall"],
                "f1_score": xgb_metrics["f1_score"],
                "roc_auc": xgb_metrics["roc_auc"],
                "pr_auc": xgb_metrics["pr_auc"],
                "brier_score": xgb_metrics["brier_score"]
            })

            # Generate and log Confusion Matrix Artifact
            cm = np.array(xgb_metrics["confusion_matrix"])
            fig, ax = plt.subplots(figsize=(5, 4))
            cax = ax.matshow(cm, cmap="Blues")
            fig.colorbar(cax)
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", color="black", fontsize=12)
            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(["Retained", "Churned"])
            ax.set_yticklabels(["Retained", "Churned"])
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")
            ax.set_title("XGBoost Confusion Matrix")
            plt.tight_layout()

            cm_path = MODELS_DIR / "confusion_matrix.png"
            fig.savefig(cm_path)
            plt.close(fig)
            mlflow.log_artifact(str(cm_path))

            # Log model binary
            model_path = MODELS_DIR / "churn_xgb_model.joblib"
            if model_path.exists():
                mlflow.log_artifact(str(model_path))

            logger.info(f"Successfully logged churn run to MLflow (Run ID: {run_id}).")
            return run_id

    def log_clv_experiment(self) -> str:
        """Logs the Customer Lifetime Value regression run to MLflow."""
        meta_path = MODELS_DIR / "clv_metrics.json"
        if not meta_path.exists():
            raise FileNotFoundError("CLV metrics artifact missing.")

        with open(meta_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        run_name = "GradientBoosting_CLV_Regressor_v1.0"
        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id
            logger.info(f"Logging CLV MLflow run {run_id} ({run_name})...")

            mlflow.log_params({
                "model_type": "GradientBoostingRegressor",
                "n_estimators": 160,
                "learning_rate": 0.07,
                "max_depth": 5
            })

            mlflow.log_metrics({
                "rmse": metrics["rmse"],
                "mae": metrics["mae"],
                "r2_score": metrics["r2_score"],
                "mape_percent": metrics["mape_percent"]
            })

            model_path = MODELS_DIR / "clv_model.joblib"
            if model_path.exists():
                mlflow.log_artifact(str(model_path))

            logger.info(f"Successfully logged CLV run to MLflow (Run ID: {run_id}).")
            return run_id

if __name__ == "__main__":
    tracker = MLflowTracker()
    tracker.log_churn_experiment()
    tracker.log_clv_experiment()
