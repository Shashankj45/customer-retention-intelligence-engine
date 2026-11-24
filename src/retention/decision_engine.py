"""
Retention Strategy Decision Engine.
Rule-based recommendation engine synthesizing Churn Risk, CLV Tier, and Root Causes.
Estimates expected saved revenue, intervention costs, and net ROI for each customer.
"""

import uuid
from typing import Dict, List, Any
import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA_DIR
from src.utils.logger import get_logger
from src.database.connection import db_manager

logger = get_logger("retention_decision_engine")

class RetentionDecisionEngine:
    """Assigns personalized retention interventions and calculates expected financial ROI."""

    def __init__(self):
        pass

    def generate_recommendations(self) -> pd.DataFrame:
        """Merges predictions, applies rule-based decision trees, and prioritizes outreach."""
        logger.info("Generating personalized retention strategies and ROI estimations...")

        # 1. Fetch tables
        cust_df = db_manager.execute_query("SELECT customer_id, customer_name, subscription_tier, contract_type FROM customers")
        churn_df = db_manager.execute_query("SELECT customer_id, churn_probability, predicted_churn, risk_tier FROM churn_predictions")
        clv_df = db_manager.execute_query("SELECT customer_id, historical_revenue, predicted_clv_12m, clv_tier FROM clv_predictions")
        feat_df = pd.read_parquet(PROCESSED_DATA_DIR / "customer_features.parquet")[
            ["customer_id", "total_tickets", "avg_csat_score", "days_since_last_session", "billing_sessions_count"]
        ]

        # Merge
        merged = cust_df.merge(churn_df, on="customer_id", how="inner")
        merged = merged.merge(clv_df, on="customer_id", how="inner")
        merged = merged.merge(feat_df, on="customer_id", how="inner")

        recommendations = []
        for _, row in merged.iterrows():
            cid = row["customer_id"]
            risk = row["risk_tier"]
            prob = float(row["churn_probability"])
            clv = float(row["predicted_clv_12m"])
            clv_tier = row["clv_tier"]
            contract = row["contract_type"]
            csat = float(row["avg_csat_score"])
            tickets = int(row["total_tickets"])
            inactivity = float(row["days_since_last_session"])

            # Rule-based decision logic
            if "Platinum" in clv_tier or "Gold" in clv_tier:
                if risk in ["Critical Risk", "High Risk"]:
                    strategy = "Executive Concierge & VIP Annual Upgrade"
                    channel = "Direct Account Exec Call"
                    cost = 75.0
                    success_rate = 0.60
                elif csat < 3.0:
                    strategy = "Dedicated Technical Support SLA Escalation"
                    channel = "Senior Solutions Engineer Call"
                    cost = 50.0
                    success_rate = 0.55
                else:
                    strategy = "Executive Business Review (EBR) & Roadmap Preview"
                    channel = "Quarterly Business Review"
                    cost = 30.0
                    success_rate = 0.40
            elif risk in ["Critical Risk", "High Risk"]:
                if csat < 3.0 or tickets >= 2:
                    strategy = "Priority Support Resolution & Account Health Check"
                    channel = "Priority Support Outreach"
                    cost = 35.0
                    success_rate = 0.50
                elif contract == "Month-to-Month":
                    strategy = "20% Annual Contract Commitment Incentive"
                    channel = "In-App Modal & Email Campaign"
                    cost = 25.0
                    success_rate = 0.45
                else:
                    strategy = "Feature Adoption Audit & Custom Workflow Guide"
                    channel = "Customer Success Email Sequence"
                    cost = 15.0
                    success_rate = 0.35
            elif risk == "Medium Risk":
                if inactivity > 10:
                    strategy = "Re-engagement Nudge: Inactive Feature Spotlight"
                    channel = "Automated Email & Push Notification"
                    cost = 5.0
                    success_rate = 0.25
                else:
                    strategy = "Loyalty Engagement: Community & Best Practice Tips"
                    channel = "In-App Product Guide"
                    cost = 5.0
                    success_rate = 0.20
            else:
                strategy = "Standard Customer Advocacy & Satisfaction Survey"
                channel = "Automated Bi-Annual Survey"
                cost = 0.0
                success_rate = 0.05

            # Financial calculations
            # Expected Saved Revenue = Churn Probability * Predicted CLV * Campaign Success Rate
            saved_revenue = round(prob * clv * success_rate, 2)
            net_roi = round(saved_revenue - cost, 2)

            recommendations.append({
                "recommendation_id": f"REC-{uuid.uuid4().hex[:8].upper()}",
                "customer_id": cid,
                "customer_name": row["customer_name"],
                "risk_tier": risk,
                "churn_probability": prob,
                "predicted_clv_12m": clv,
                "clv_tier": clv_tier,
                "recommended_strategy": strategy,
                "intervention_channel": channel,
                "estimated_retention_cost": cost,
                "expected_saved_revenue": saved_revenue,
                "estimated_net_roi": net_roi,
                "priority_rank": 0 # Will be assigned below
            })

        rec_df = pd.DataFrame(recommendations)
        
        # Sort and rank by Net ROI descending
        rec_df = rec_df.sort_values(by=["estimated_net_roi", "expected_saved_revenue"], ascending=[False, False]).reset_index(drop=True)
        rec_df["priority_rank"] = rec_df.index + 1

        # Save to database
        db_cols = [
            "recommendation_id", "customer_id", "risk_tier", "recommended_strategy",
            "intervention_channel", "estimated_retention_cost", "expected_saved_revenue",
            "estimated_net_roi", "priority_rank"
        ]
        rec_df[db_cols].to_sql("retention_recommendations", db_manager.engine, if_exists="replace", index=False)
        rec_df.to_parquet(PROCESSED_DATA_DIR / "retention_recommendations.parquet", index=False)

        total_saved = rec_df["expected_saved_revenue"].sum()
        total_cost = rec_df["estimated_retention_cost"].sum()
        logger.info(f"Generated {len(rec_df):,} recommendations. Total Potential Saved Revenue: ${total_saved:,.2f} against ${total_cost:,.2f} campaign cost.")
        return rec_df

if __name__ == "__main__":
    engine = RetentionDecisionEngine()
    df = engine.generate_recommendations()
    print("Top 3 Retention Recommendations:\n", df[["customer_name", "risk_tier", "clv_tier", "recommended_strategy", "expected_saved_revenue", "estimated_net_roi"]].head(3))
