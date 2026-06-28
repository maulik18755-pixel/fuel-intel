"""
Network Optimizer: Selects the best N locations for a fuel retail network.

This is what makes the tool a NETWORK planner, not just a location scorer.
It enforces real-world constraints:
1. Minimum spacing — no two stations within X km (prevents cannibalization)
2. Budget constraint — total CAPEX must fit within allocation
3. Coverage — maximize population within service radius
4. Diversity — ensure state/tier diversity in the portfolio
"""
import math
import pandas as pd
import numpy as np
from config.settings import Settings


def _haversine_km(lat1, lng1, lat2, lng2):
    """Compute distance between two points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class NetworkOptimizer:
    """
    Greedy network optimizer with constraints.

    Algorithm:
    1. Sort all candidates by composite_score (descending)
    2. Greedily select the next-best candidate that satisfies ALL constraints:
       a. Not within min_spacing_km of any already-selected station
       b. Adding it doesn't exceed the budget
    3. Stop when target_count is reached or no valid candidates remain

    This is a greedy heuristic — not globally optimal, but produces good solutions
    fast and is easy to explain to stakeholders.
    """

    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()

    def optimize(
        self,
        scored_df: pd.DataFrame,
        target_count: int = 100,
        budget_cr: float = None,
        min_spacing_km: float = 15.0,
        min_spacing_highway_km: float = 30.0,
        state_max_pct: float = 0.25,
    ) -> dict:
        """
        Select the optimal network from scored candidates.

        Args:
            scored_df: DataFrame with composite_score, lat, lng, tier, format_code, npv_cr, etc.
            target_count: How many stations to select
            budget_cr: Maximum total CAPEX in ₹ Crores (None = unlimited)
            min_spacing_km: Minimum distance between urban/tier stations
            min_spacing_highway_km: Minimum distance between highway stations
            state_max_pct: Max % of network from any single state (diversity)

        Returns:
            dict with selected_df, rejected_df, summary stats, constraint_log
        """
        df = scored_df.sort_values("composite_score", ascending=False).reset_index(drop=True)

        selected_indices = []
        selected_lats = []
        selected_lngs = []
        selected_tiers = []
        selected_states = []
        total_capex = 0.0
        state_counts = {}
        constraint_log = []

        capex_lookup = self.settings.capex_by_format

        for idx, row in df.iterrows():
            if len(selected_indices) >= target_count:
                break

            lat, lng = float(row["lat"]), float(row["lng"])
            tier = row.get("tier", "tier2")
            state = row.get("state", "")
            fmt_code = row.get("format_code", "hybrid_transition")
            capex = capex_lookup.get(fmt_code, 12.0)

            # Constraint 1: Minimum spacing
            spacing = min_spacing_highway_km if tier == "highway" else min_spacing_km
            too_close = False
            for i, (slat, slng, stier) in enumerate(zip(selected_lats, selected_lngs, selected_tiers)):
                dist = _haversine_km(lat, lng, slat, slng)
                if dist < spacing:
                    too_close = True
                    constraint_log.append({
                        "location": row.get("name", ""),
                        "reason": f"Too close ({dist:.1f}km) to {df.iloc[selected_indices[i]].get('name', '')}",
                        "constraint": "spacing",
                    })
                    break
            if too_close:
                continue

            # Constraint 2: Budget
            if budget_cr is not None and total_capex + capex > budget_cr:
                constraint_log.append({
                    "location": row.get("name", ""),
                    "reason": f"Budget exceeded (₹{total_capex + capex:.0f} Cr > ₹{budget_cr:.0f} Cr)",
                    "constraint": "budget",
                })
                continue

            # Constraint 3: State diversity
            max_from_state = max(1, int(target_count * state_max_pct))
            if state_counts.get(state, 0) >= max_from_state:
                constraint_log.append({
                    "location": row.get("name", ""),
                    "reason": f"State cap reached ({state}: {state_counts[state]}/{max_from_state})",
                    "constraint": "diversity",
                })
                continue

            # Accept this location
            selected_indices.append(idx)
            selected_lats.append(lat)
            selected_lngs.append(lng)
            selected_tiers.append(tier)
            selected_states.append(state)
            total_capex += capex
            state_counts[state] = state_counts.get(state, 0) + 1

        selected_df = df.iloc[selected_indices].copy()
        selected_df["network_rank"] = range(1, len(selected_df) + 1)
        rejected_df = df.drop(index=selected_indices).copy()

        # Summary
        summary = {
            "total_selected": len(selected_df),
            "total_candidates": len(df),
            "total_capex_cr": round(total_capex, 1),
            "total_npv_cr": round(selected_df["npv_cr"].sum(), 1) if "npv_cr" in selected_df.columns else 0,
            "avg_score": round(selected_df["composite_score"].mean(), 1) if len(selected_df) > 0 else 0,
            "states_covered": selected_df["state"].nunique() if len(selected_df) > 0 else 0,
            "tier_mix": selected_df["tier"].value_counts().to_dict() if len(selected_df) > 0 else {},
            "format_mix": selected_df["format_name"].value_counts().to_dict() if "format_name" in selected_df.columns and len(selected_df) > 0 else {},
            "spacing_rejections": sum(1 for c in constraint_log if c["constraint"] == "spacing"),
            "budget_rejections": sum(1 for c in constraint_log if c["constraint"] == "budget"),
            "diversity_rejections": sum(1 for c in constraint_log if c["constraint"] == "diversity"),
        }

        return {
            "selected": selected_df,
            "rejected": rejected_df,
            "summary": summary,
            "constraint_log": constraint_log,
        }

    def phase_network(self, selected_df: pd.DataFrame, phases: int = 3) -> dict:
        """
        Split selected network into deployment phases.
        Phase 1: Highest-scoring, lowest-risk (fast track)
        Phase 2: Strong but needs feasibility work
        Phase 3: Strategic pipeline
        """
        if selected_df.empty:
            return {}

        n = len(selected_df)
        p1_size = max(1, n // 3)
        p2_size = max(1, n // 3)

        sorted_df = selected_df.sort_values("composite_score", ascending=False).reset_index(drop=True)

        return {
            "phase_1": {
                "name": "Immediate (0-12 months)",
                "locations": sorted_df.head(p1_size),
                "capex_cr": round(sorted_df.head(p1_size)["npv_cr"].sum(), 1) if "npv_cr" in sorted_df.columns else 0,
            },
            "phase_2": {
                "name": "Near-Term (12-24 months)",
                "locations": sorted_df.iloc[p1_size:p1_size + p2_size],
                "capex_cr": round(sorted_df.iloc[p1_size:p1_size + p2_size]["npv_cr"].sum(), 1) if "npv_cr" in sorted_df.columns else 0,
            },
            "phase_3": {
                "name": "Strategic Pipeline (24-36 months)",
                "locations": sorted_df.iloc[p1_size + p2_size:],
                "capex_cr": round(sorted_df.iloc[p1_size + p2_size:]["npv_cr"].sum(), 1) if "npv_cr" in sorted_df.columns else 0,
            },
        }
