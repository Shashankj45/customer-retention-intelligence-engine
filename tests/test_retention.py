"""
Tests for Retention Strategy Decision Engine and ROI Scenario Simulator.
"""

import pytest
from src.retention.roi_simulator import RetentionROISimulator

def test_roi_simulator_financial_consistency():
    sim = RetentionROISimulator()
    result = sim.run_simulation(
        targeted_tiers=["Critical Risk", "High Risk"],
        contact_cost_per_user=20.0,
        discount_percent=10.0,
        acceptance_rate_percent=40.0
    )

    assert "targeted_customers" in result
    assert "retained_customers" in result
    assert "gross_revenue_saved" in result
    assert "total_campaign_cost" in result
    assert "net_profit_saved" in result

    # Financial equality: Net Benefit = Gross Saved - Total Cost
    expected_net = round(result["gross_revenue_saved"] - result["total_campaign_cost"], 2)
    assert abs(result["net_profit_saved"] - expected_net) < 1.0

    # Retained customers must not exceed targeted customers
    assert result["retained_customers"] <= result["targeted_customers"]
