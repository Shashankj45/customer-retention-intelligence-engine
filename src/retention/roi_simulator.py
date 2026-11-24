"""
Retention ROI What-If Scenario Simulator.
Simulates financial returns for custom retention campaign configurations:
Targeting risk tiers, outreach contact costs, discount percentages, and acceptance rates.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from src.config import PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("roi_simulator")

class RetentionROISimulator:
    """Simulates financial and customer retention outcomes for marketing and customer success leaders."""

    def __init__(self):
        self.data_path = PROCESSED_DATA_DIR / "retention_recommendations.parquet"

    def run_simulation(
        self,
        targeted_tiers: List[str] = None,
        contact_cost_per_user: float = 25.0,
        discount_percent: float = 15.0,
        acceptance_rate_percent: float = 45.0,
        min_clv_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """Runs what-if simulation and computes financial return metrics."""
        if not self.data_path.exists():
            from src.retention.decision_engine import RetentionDecisionEngine
            engine = RetentionDecisionEngine()
            df = engine.generate_recommendations()
        else:
            df = pd.read_parquet(self.data_path)

        targeted_tiers = targeted_tiers or ["Critical Risk", "High Risk"]
        acceptance_rate = acceptance_rate_percent / 100.0
        discount_rate = discount_percent / 100.0

        # Filter targeted audience
        cohort = df[
            (df["risk_tier"].isin(targeted_tiers)) &
            (df["predicted_clv_12m"] >= min_clv_threshold)
        ].copy()

        cohort_size = len(cohort)
        if cohort_size == 0:
            return {
                "targeted_customers": 0,
                "retained_customers": 0,
                "gross_revenue_saved": 0.0,
                "outreach_cost": 0.0,
                "discount_cost": 0.0,
                "total_campaign_cost": 0.0,
                "net_profit_saved": 0.0,
                "roi_percentage": 0.0,
                "payback_months": 0.0
            }

        # Calculations
        # Expected retained customers = Sum(churn_prob * acceptance_rate)
        expected_retained_customers = int(np.round((cohort["churn_probability"] * acceptance_rate).sum()))

        # Gross Saved Revenue = Sum(churn_prob * predicted_clv * acceptance_rate)
        gross_saved_revenue = float(np.round((cohort["churn_probability"] * cohort["predicted_clv_12m"] * acceptance_rate).sum(), 2))

        # Total outreach cost
        outreach_cost = float(np.round(cohort_size * contact_cost_per_user, 2))

        # Discount cost = Discount on expected retained customers' 12M revenue
        discount_cost = float(np.round(gross_saved_revenue * discount_rate, 2))

        # Total cost
        total_campaign_cost = float(np.round(outreach_cost + discount_cost, 2))

        # Net Profit Saved
        net_profit_saved = float(np.round(gross_saved_revenue - total_campaign_cost, 2))

        # ROI percentage
        roi_pct = float(np.round((net_profit_saved / max(1.0, total_campaign_cost)) * 100.0, 2))

        # Payback period in months: Total Cost / (Gross Saved Revenue / 12)
        monthly_saved = gross_saved_revenue / 12.0
        payback_months = float(np.round(total_campaign_cost / max(1.0, monthly_saved), 1)) if monthly_saved > 0 else 0.0

        results = {
            "targeted_customers": cohort_size,
            "retained_customers": expected_retained_customers,
            "gross_revenue_saved": gross_saved_revenue,
            "outreach_cost": outreach_cost,
            "discount_cost": discount_cost,
            "total_campaign_cost": total_campaign_cost,
            "net_profit_saved": net_profit_saved,
            "roi_percentage": roi_pct,
            "payback_months": payback_months,
            "cohort_details": cohort[[
                "customer_name", "risk_tier", "churn_probability", "predicted_clv_12m",
                "recommended_strategy", "expected_saved_revenue"
            ]].head(100).to_dict(orient="records")
        }

        logger.info(
            f"Simulation: {cohort_size:,} targeted -> {expected_retained_customers:,} retained | "
            f"Gross Saved: ${gross_saved_revenue:,.2f} | Total Cost: ${total_campaign_cost:,.2f} | "
            f"Net Benefit: ${net_profit_saved:,.2f} ({roi_pct:.1f}% ROI)"
        )
        return results

if __name__ == "__main__":
    sim = RetentionROISimulator()
    res = sim.run_simulation(targeted_tiers=["Critical Risk", "High Risk"], contact_cost_per_user=25.0, discount_percent=15.0, acceptance_rate_percent=45.0)
    print("Simulation Output:\n", {k: v for k, v in res.items() if k != "cohort_details"})
