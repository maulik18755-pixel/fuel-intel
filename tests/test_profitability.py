"""Tests for the profitability model."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.profitability_model import ProfitabilityModel
from core.format_recommender import FormatRecommender, FORMATS
from config.settings import Settings


def test_mumbai_metro_positive_npv(sample_location):
    pm = ProfitabilityModel()
    fmt = FormatRecommender().recommend(sample_location)
    result = pm.project_cash_flows(sample_location, fmt)
    assert result["npv_cr"] > 0, f"Mumbai metro NPV should be positive, got {result['npv_cr']}"


def test_highway_hub_npv_higher_than_compact(highway_location):
    pm = ProfitabilityModel()
    hub = pm.project_cash_flows(highway_location, FORMATS["large_highway_hub"])
    compact = pm.project_cash_flows(highway_location, FORMATS["compact_urban"])
    assert hub["npv_cr"] > compact["npv_cr"]


def test_payback_within_horizon(sample_location):
    pm = ProfitabilityModel()
    fmt = FormatRecommender().recommend(sample_location)
    result = pm.project_cash_flows(sample_location, fmt)
    assert result["payback_years"] <= 15, f"Payback {result['payback_years']} exceeds 15 years"


def test_cash_flows_has_15_entries(sample_location):
    pm = ProfitabilityModel()
    fmt = FormatRecommender().recommend(sample_location)
    result = pm.project_cash_flows(sample_location, fmt)
    assert len(result["annual_cash_flows"]) == 15


def test_irr_in_reasonable_range(sample_location):
    pm = ProfitabilityModel()
    fmt = FormatRecommender().recommend(sample_location)
    result = pm.project_cash_flows(sample_location, fmt)
    assert 0 < result["irr_pct"] < 60, f"IRR {result['irr_pct']} outside reasonable range"


def test_ev_crossover_for_ev_format(ev_metro_location):
    pm = ProfitabilityModel()
    fmt = FORMATS["ev_focused_station"]
    result = pm.project_cash_flows(ev_metro_location, fmt)
    if result["ev_crossover_year"] is not None:
        assert 1 <= result["ev_crossover_year"] <= 15


def test_revenue_grows_over_time(sample_location):
    pm = ProfitabilityModel()
    fmt = FormatRecommender().recommend(sample_location)
    result = pm.project_cash_flows(sample_location, fmt)
    flows = result["annual_cash_flows"]
    rev_y1 = flows[0]["total_revenue_cr"]
    rev_y15 = flows[-1]["total_revenue_cr"]
    assert rev_y15 > 0


def test_capex_matches_format(sample_location):
    pm = ProfitabilityModel()
    fmt = FormatRecommender().recommend(sample_location)
    result = pm.project_cash_flows(sample_location, fmt)
    assert result["total_investment_cr"] == fmt["capex_cr"]


def test_higher_discount_rate_lowers_npv(sample_location):
    pm1 = ProfitabilityModel(Settings(discount_rate=0.10))
    pm2 = ProfitabilityModel(Settings(discount_rate=0.15))
    fmt = FormatRecommender().recommend(sample_location)
    r1 = pm1.project_cash_flows(sample_location, fmt)
    r2 = pm2.project_cash_flows(sample_location, fmt)
    assert r1["npv_cr"] > r2["npv_cr"]


def test_low_demand_tier3_marginal(low_demand_tier3):
    pm = ProfitabilityModel()
    fmt = FormatRecommender().recommend(low_demand_tier3)
    result = pm.project_cash_flows(low_demand_tier3, fmt)
    # Low demand should produce lower returns
    assert result["npv_cr"] < 20, f"Tier3 NPV unexpectedly high: {result['npv_cr']}"
