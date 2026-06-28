"""Tests for the scoring engine."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.settings import Settings
from core.scoring_engine import ScoringEngine


def test_default_weights_sum_to_one():
    s = Settings()
    assert abs(sum(s.scoring_weights.values()) - 1.0) < 0.001


def test_custom_weights_normalized():
    engine = ScoringEngine({"demand": 35, "competition": 20, "income": 15, "ev_readiness": 15, "infrastructure": 10, "growth_trajectory": 5})
    assert abs(sum(engine.weights.values()) - 1.0) < 0.001


def test_competition_inversion(sample_location):
    low_comp = dict(sample_location, competition=20)
    high_comp = dict(sample_location, competition=80)
    engine = ScoringEngine()
    assert engine.score_location(low_comp)["composite_score"] > engine.score_location(high_comp)["composite_score"]


def test_score_range_bounds(sample_location):
    engine = ScoringEngine()
    result = engine.score_location(sample_location)
    assert 0 <= result["composite_score"] <= 100


def test_score_tier_high(sample_location):
    engine = ScoringEngine()
    result = engine.score_location(sample_location)
    assert result["composite_score"] >= 70
    assert result["score_tier"] == "High Potential"


def test_score_tier_low(low_demand_tier3):
    engine = ScoringEngine()
    result = engine.score_location(low_demand_tier3)
    assert result["score_tier"] in ("Low Potential", "Moderate")


def test_key_strengths_identified(sample_location):
    engine = ScoringEngine()
    result = engine.score_location(sample_location)
    assert isinstance(result["key_strengths"], list)
    assert len(result["key_strengths"]) == 2


def test_key_gaps_identified(sample_location):
    engine = ScoringEngine()
    result = engine.score_location(sample_location)
    assert isinstance(result["key_gaps"], list)
    assert len(result["key_gaps"]) == 2


def test_batch_scoring_sorted(sample_location, low_demand_tier3):
    engine = ScoringEngine()
    df = engine.score_batch([sample_location, low_demand_tier3])
    assert len(df) == 2
    scores = df["composite_score"].tolist()
    assert scores[0] >= scores[1]


def test_identical_locations_same_score(sample_location):
    engine = ScoringEngine()
    s1 = engine.score_location(dict(sample_location))
    s2 = engine.score_location(dict(sample_location))
    assert s1["composite_score"] == s2["composite_score"]


def test_sensitivity_analysis(sample_location):
    engine = ScoringEngine()
    result = engine.sensitivity_analysis(sample_location, "demand", delta_pct=20.0)
    assert result["score_if_high"] >= result["score_if_low"]
    assert result["sensitivity_magnitude"] >= 0


def test_full_sensitivity_all_pillars(sample_location):
    engine = ScoringEngine()
    results = engine.full_sensitivity(sample_location)
    assert len(results) == 6
    assert results[0]["sensitivity_magnitude"] >= results[-1]["sensitivity_magnitude"]
