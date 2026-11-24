"""
Data & Concept Drift Monitoring Engine.
Computes Population Stability Index (PSI) and Kolmogorov-Smirnov tests
to monitor feature distribution shifts and alert before model performance degrades.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, chisquare

from src.config import MODELS_DIR, PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("drift_monitor")

class DriftMonitor:
    """Detects statistical covariate shift and target concept drift."""

    def __init__(self):
        self.models_dir = MODELS_DIR

    def calculate_psi(self, expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
        """Calculates Population Stability Index between baseline and production batches."""
        # Clean NaNs
        expected = expected[~np.isnan(expected)]
        actual = actual[~np.isnan(actual)]

        if len(expected) == 0 or len(actual) == 0:
            return 0.0

        # Percentile boundaries based on expected distribution
        percentiles = np.linspace(0, 100, num_buckets + 1)
        breakpoints = np.percentile(expected, percentiles)
        breakpoints[0] -= 1e-5
        breakpoints[-1] += 1e-5

        # Counts per bucket
        expected_counts, _ = np.histogram(expected, bins=breakpoints)
        actual_counts, _ = np.histogram(actual, bins=breakpoints)

        # Proportions with small epsilon to prevent div-by-zero
        eps = 1e-4
        expected_pct = (expected_counts / len(expected)) + eps
        actual_pct = (actual_counts / len(actual)) + eps

        # Normalize to sum to 1
        expected_pct /= expected_pct.sum()
        actual_pct /= actual_pct.sum()

        psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(np.round(psi_val, 4))

    def evaluate_drift(self, batch_df: pd.DataFrame = None) -> Dict[str, Any]:
        """Runs KS-tests and PSI across core behavioral features."""
        logger.info("Evaluating feature distributions for statistical data drift...")

        baseline_df = pd.read_parquet(PROCESSED_DATA_DIR / "customer_features.parquet")

        # If no new batch passed, simulate a realistic production monitoring window
        # (e.g. recent cohort with mild variation)
        if batch_df is None:
            batch_df = baseline_df.sample(frac=0.35, random_state=123).copy()
            # Simulate slight organic shift in engagement
            batch_df["avg_session_duration"] = batch_df["avg_session_duration"] * np.random.uniform(0.95, 1.05)
            batch_df["days_since_last_session"] = batch_df["days_since_last_session"] + np.random.uniform(-1, 2, size=len(batch_df))

        monitored_features = [
            "spend_per_tenure_month", "avg_session_duration", "days_since_last_session",
            "avg_csat_score", "total_tickets", "bounce_rate"
        ]

        feature_reports = []
        overall_max_psi = 0.0

        for col in monitored_features:
            base_vals = baseline_df[col].values
            batch_vals = batch_df[col].values

            # KS test
            ks_stat, p_val = ks_2samp(base_vals, batch_vals)
            
            # PSI
            psi = self.calculate_psi(base_vals, batch_vals)
            overall_max_psi = max(overall_max_psi, psi)

            # Drift severity
            if psi >= 0.25 or p_val < 0.01:
                status = "DRIFT_DETECTED"
            elif psi >= 0.10:
                status = "MODERATE_SHIFT"
            else:
                status = "STABLE"

            feature_reports.append({
                "feature": col,
                "ks_statistic": round(float(ks_stat), 4),
                "p_value": round(float(p_val), 4),
                "psi": psi,
                "status": status
            })

        # Overall Status
        if overall_max_psi >= 0.25:
            overall_status = "ALERT_HIGH_DRIFT"
        elif overall_max_psi >= 0.10:
            overall_status = "WARNING_MODERATE_DRIFT"
        else:
            overall_status = "HEALTHY_STABLE"

        report = {
            "overall_status": overall_status,
            "max_psi": round(overall_max_psi, 4),
            "baseline_samples": len(baseline_df),
            "batch_samples": len(batch_df),
            "feature_drifts": feature_reports
        }

        # Save to models dir
        with open(self.models_dir / "drift_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)

        logger.info(f"Drift Monitoring Complete: Overall Status = {overall_status} (Max PSI = {overall_max_psi})")
        return report

if __name__ == "__main__":
    monitor = DriftMonitor()
    res = monitor.evaluate_drift()
    print("Drift Report Summary:\n", {k: v for k, v in res.items() if k != "feature_drifts"})
