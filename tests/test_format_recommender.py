"""Tests for the format recommender."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.format_recommender import FormatRecommender, FORMATS


def test_highway_gets_large_hub(highway_location):
    r = FormatRecommender()
    result = r.recommend(highway_location)
    assert result["code"] == "large_highway_hub"


def test_ev_metro_gets_ev_focused(ev_metro_location):
    r = FormatRecommender()
    result = r.recommend(ev_metro_location)
    assert result["code"] == "ev_focused_station"


def test_high_demand_metro_gets_urban(sample_location):
    loc = dict(sample_location, ev_readiness=50, demand=85, income=80)
    r = FormatRecommender()
    result = r.recommend(loc)
    assert result["code"] in ("urban_full_service", "ev_focused_station")


def test_low_demand_gets_compact(low_demand_tier3):
    r = FormatRecommender()
    result = r.recommend(low_demand_tier3)
    assert result["code"] == "compact_urban"


def test_moderate_gets_hybrid():
    loc = {"tier": "tier2", "demand": 60, "competition": 50, "income": 55, "ev_readiness": 35, "infrastructure": 60, "growth_trajectory": 50}
    r = FormatRecommender()
    result = r.recommend(loc)
    assert result["code"] == "hybrid_transition"


def test_result_has_required_keys(sample_location):
    r = FormatRecommender()
    result = r.recommend(sample_location)
    for key in ("code", "name", "icon", "capex_cr", "reasoning"):
        assert key in result, f"Missing key: {key}"


def test_transition_plan_present(sample_location):
    r = FormatRecommender()
    result = r.recommend(sample_location)
    tp = result.get("transition_plan", {})
    assert isinstance(tp, dict)
    assert "year_3" in tp
    assert "year_5" in tp
    assert "year_10" in tp


def test_all_five_formats_reachable():
    r = FormatRecommender()
    reached = set()
    test_cases = [
        {"tier": "highway", "demand": 70, "competition": 25, "income": 60, "ev_readiness": 40, "infrastructure": 85, "growth_trajectory": 60},
        {"tier": "metro", "demand": 80, "competition": 40, "income": 90, "ev_readiness": 80, "infrastructure": 80, "growth_trajectory": 75},
        {"tier": "metro", "demand": 85, "competition": 40, "income": 80, "ev_readiness": 50, "infrastructure": 75, "growth_trajectory": 60, "composite_score": 72},
        {"tier": "tier3", "demand": 30, "competition": 60, "income": 35, "ev_readiness": 10, "infrastructure": 40, "growth_trajectory": 30, "composite_score": 30},
        {"tier": "tier2", "demand": 60, "competition": 50, "income": 55, "ev_readiness": 35, "infrastructure": 60, "growth_trajectory": 50},
    ]
    for loc in test_cases:
        result = r.recommend(loc)
        reached.add(result["code"])
    assert len(reached) == 5, f"Only reached {len(reached)} formats: {reached}"
