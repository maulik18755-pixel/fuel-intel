"""
Platform-wide configurable settings.
All financial values in ₹ Crores unless noted.
"""
from pydantic import BaseModel, model_validator
from typing import Dict, Tuple


class Settings(BaseModel):
    # --- Scoring weights (must sum to 1.0) ---
    scoring_weights: Dict[str, float] = {
        "demand": 0.30,
        "competition": 0.20,
        "income": 0.15,
        "ev_readiness": 0.15,
        "infrastructure": 0.10,
        "growth_trajectory": 0.10,
    }

    # --- Financial parameters ---
    discount_rate: float = 0.12
    npv_horizon_years: int = 15
    fuel_decline_start_year: int = 5
    fuel_decline_rate_annual: float = 0.02
    ev_growth_rate_annual: float = 0.15
    fuel_margin_per_litre: float = 3.5       # ₹
    ev_margin_per_kwh: float = 10.0          # ₹
    convenience_revenue_per_sqft_annual: float = 1200.0  # ₹
    opex_pct_of_capex: float = 0.035
    retail_revenue_growth_annual: float = 0.05
    ancillary_revenue_pct_of_fuel: float = 0.02

    # --- CAPEX by format (₹ Crores) ---
    capex_by_format: Dict[str, float] = {
        "large_highway_hub": 22.0,
        "urban_full_service": 18.0,
        "ev_focused_station": 15.0,
        "hybrid_transition": 12.0,
        "compact_urban": 8.0,
    }

    # --- Land lease by tier (₹ Lakhs/year) ---
    land_lease_by_tier: Dict[str, float] = {
        "metro": 35.0,
        "tier2": 18.0,
        "highway": 12.0,
        "tier3": 8.0,
        "emerging": 22.0,
    }

    # --- Staff cost by tier: (headcount, ₹ Lakhs/year per person) ---
    staff_by_tier: Dict[str, Tuple[int, float]] = {
        "metro": (12, 3.0),
        "tier2": (10, 2.5),
        "highway": (15, 2.5),
        "tier3": (8, 2.0),
        "emerging": (10, 2.8),
    }

    # --- Vehicle mix by tier: (car_pct, commercial_pct) ---
    vehicle_mix_by_tier: Dict[str, Tuple[float, float]] = {
        "metro": (0.70, 0.30),
        "tier2": (0.65, 0.35),
        "highway": (0.40, 0.60),
        "tier3": (0.60, 0.40),
        "emerging": (0.65, 0.35),
    }

    # --- Fueling probability by tier ---
    fueling_probability: Dict[str, float] = {
        "metro": 0.50,
        "tier2": 0.55,
        "highway": 0.70,
        "tier3": 0.55,
        "emerging": 0.50,
    }

    # --- Avg fill litres ---
    avg_fill_car_litres: float = 25.0
    avg_fill_commercial_litres: float = 80.0

    # --- EV charging ---
    ev_sessions_per_charger_day_y1: float = 4.0
    ev_sessions_per_charger_day_y10: float = 12.0
    avg_kwh_per_session: float = 30.0
    ev_charger_cost_cr_each: float = 0.15
    ev_charger_replacement_year: int = 8
    ev_charger_replacement_pct: float = 0.20

    # --- Utilities ---
    utilities_base_cr: float = 0.02
    utilities_per_charger_cr: float = 0.015

    @model_validator(mode="after")
    def normalize_weights(self):
        w = self.scoring_weights
        total = sum(w.values())
        if total > 0 and abs(total - 1.0) > 0.001:
            self.scoring_weights = {k: v / total for k, v in w.items()}
        return self

    def get_capex(self, format_code: str) -> float:
        return self.capex_by_format.get(format_code, 12.0)

    def get_land_lease(self, tier: str) -> float:
        return self.land_lease_by_tier.get(tier, 15.0)

    def get_staff_cost(self, tier: str) -> Tuple[int, float]:
        return self.staff_by_tier.get(tier, (10, 2.5))

    def get_vehicle_mix(self, tier: str) -> Tuple[float, float]:
        return self.vehicle_mix_by_tier.get(tier, (0.60, 0.40))

    def get_fueling_prob(self, tier: str) -> float:
        return self.fueling_probability.get(tier, 0.55)
