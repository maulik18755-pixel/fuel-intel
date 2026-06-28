"""
Location Attractiveness Scoring Engine.
Scores candidate locations on 6 pillars, producing a composite 0-100 score.
"""
import pandas as pd
from config.settings import Settings

PILLAR_NAMES = {
    "demand": "Demand Intensity",
    "competition": "Competition Gap",
    "income": "Income & Spending Power",
    "ev_readiness": "EV Readiness",
    "infrastructure": "Infrastructure Quality",
    "growth_trajectory": "Growth Trajectory",
}


class ScoringEngine:
    def __init__(self, weights: dict = None):
        self.settings = Settings()
        if weights:
            total = sum(weights.values())
            self.weights = {k: v / total for k, v in weights.items()} if total > 0 else self.settings.scoring_weights
        else:
            self.weights = self.settings.scoring_weights

    def score_location(self, location: dict) -> dict:
        """Score a single location. Returns the location dict enriched with scoring data."""
        result = dict(location)

        pillars = {}
        for key in self.weights:
            raw = float(location.get(key, 50))
            if key == "competition":
                pillars[key] = max(0, min(100, 100 - raw))
            else:
                pillars[key] = max(0, min(100, raw))

        composite = sum(pillars[k] * self.weights[k] for k in self.weights)
        composite = int(max(0, min(100, round(composite))))

        sorted_pillars = sorted(pillars.items(), key=lambda x: x[1], reverse=True)
        strengths = [p[0] for p in sorted_pillars[:2]]
        gaps = [p[0] for p in sorted_pillars[-2:]]

        if composite >= 70:
            tier = "High Potential"
        elif composite >= 45:
            tier = "Moderate"
        else:
            tier = "Low Potential"

        result["composite_score"] = composite
        result["pillar_scores"] = pillars
        result["score_tier"] = tier
        result["key_strengths"] = strengths
        result["key_gaps"] = gaps
        result["competition_inverted"] = pillars.get("competition", 50)
        return result

    def score_batch(self, locations: list) -> pd.DataFrame:
        """Score all locations, return DataFrame sorted by composite_score descending."""
        scored = [self.score_location(loc) for loc in locations]
        df = pd.DataFrame(scored)
        if "composite_score" in df.columns:
            df = df.sort_values("composite_score", ascending=False).reset_index(drop=True)
        return df

    def sensitivity_analysis(self, location: dict, pillar: str, delta_pct: float = 20.0) -> dict:
        """Show how the composite score changes when one pillar moves ±delta_pct%."""
        base = self.score_location(location)
        base_score = base["composite_score"]

        low_loc = dict(location)
        raw_val = float(location.get(pillar, 50))
        low_loc[pillar] = max(0, raw_val * (1 - delta_pct / 100))
        low_score = self.score_location(low_loc)["composite_score"]

        high_loc = dict(location)
        high_loc[pillar] = min(100, raw_val * (1 + delta_pct / 100))
        high_score = self.score_location(high_loc)["composite_score"]

        return {
            "pillar": pillar,
            "pillar_name": PILLAR_NAMES.get(pillar, pillar),
            "base_score": base_score,
            "score_if_low": low_score,
            "score_if_high": high_score,
            "sensitivity_magnitude": high_score - low_score,
        }

    def full_sensitivity(self, location: dict, delta_pct: float = 20.0) -> list:
        """Run sensitivity analysis on all 6 pillars."""
        results = []
        for pillar in self.weights:
            results.append(self.sensitivity_analysis(location, pillar, delta_pct))
        return sorted(results, key=lambda x: x["sensitivity_magnitude"], reverse=True)

    def compare_weight_scenarios(self, locations: list, scenarios: dict) -> pd.DataFrame:
        """
        Score locations under different weight sets.
        scenarios = {"Base Case": {weights}, "EV-Heavy": {weights}, ...}
        """
        rows = []
        for loc in locations:
            row = {"name": loc.get("name", ""), "state": loc.get("state", ""), "tier": loc.get("tier", "")}
            for scenario_name, weights in scenarios.items():
                engine = ScoringEngine(weights)
                scored = engine.score_location(loc)
                row[f"{scenario_name}_score"] = scored["composite_score"]
                row[f"{scenario_name}_tier"] = scored["score_tier"]
            rows.append(row)

        df = pd.DataFrame(rows)
        first_scenario = list(scenarios.keys())[0]
        sort_col = f"{first_scenario}_score"
        if sort_col in df.columns:
            df = df.sort_values(sort_col, ascending=False).reset_index(drop=True)
        return df


def load_locations_from_csv(filepath: str = "data/seed/scored_locations.csv") -> list:
    """Load scored locations from CSV seed file, skipping comment headers."""
    df = pd.read_csv(filepath, comment="#")
    return df.to_dict("records")
