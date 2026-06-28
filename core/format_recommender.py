"""
Station Format Recommendation Engine.
Maps location attributes to one of 5 station formats via a rule-based decision tree.
"""

FORMATS = {
    "large_highway_hub": {
        "code": "large_highway_hub",
        "name": "Large Highway Hub",
        "icon": "🛣️",
        "fuel_dispensing_points": (8, 12),
        "ev_chargers": (4, 6),
        "charger_type": "DC Fast (60-120kW)",
        "retail_sqft": (1200, 1800),
        "amenities": ["Convenience Store", "Food Court", "Restrooms", "Driver Lounge", "ATM", "Air & Water"],
        "footprint_sqft": (25000, 40000),
        "capex_cr": 22.0,
        "description": "Full-service highway hub with multi-fuel, EV fast charging, and extensive amenities for long-haul travellers.",
        "transition_plan": {
            "year_3": "Add 2 additional DC fast chargers based on utilization data",
            "year_5": "Install battery swap bay; expand food court seating",
            "year_10": "Convert 4 fuel dispensing points to additional EV chargers based on demand shift",
        },
    },
    "urban_full_service": {
        "code": "urban_full_service",
        "name": "Urban Full-Service",
        "icon": "🏙️",
        "fuel_dispensing_points": (6, 8),
        "ev_chargers": (4, 8),
        "charger_type": "Mixed AC (7kW) + DC (60kW)",
        "retail_sqft": (800, 1200),
        "amenities": ["Convenience Store", "Car Wash", "Air & Water", "Digital Payment Kiosk"],
        "footprint_sqft": (15000, 25000),
        "capex_cr": 18.0,
        "description": "Urban station combining fuel retail with growing EV charging capacity and convenience retail.",
        "transition_plan": {
            "year_3": "Add 4 DC fast chargers to supplement AC units",
            "year_5": "Expand retail space; add premium lounge for EV customers",
            "year_10": "Target 50% EV / 50% fuel split; evaluate further fuel-to-EV conversion",
        },
    },
    "ev_focused_station": {
        "code": "ev_focused_station",
        "name": "EV-Focused Station",
        "icon": "⚡",
        "fuel_dispensing_points": (2, 4),
        "ev_chargers": (8, 16),
        "charger_type": "DC Ultra-Fast (120-350kW)",
        "retail_sqft": (600, 1000),
        "amenities": ["Premium Lounge", "Wi-Fi", "Vending Machines", "Battery Diagnostics", "Digital Payment"],
        "footprint_sqft": (10000, 20000),
        "capex_cr": 15.0,
        "description": "Primarily EV charging station with ultra-fast chargers and premium customer experience. Minimal fuel retained for transition period.",
        "transition_plan": {
            "year_3": "Phase out 2 fuel dispensing points; add 4 ultra-fast chargers",
            "year_5": "Full EV conversion; remove remaining fuel infrastructure",
            "year_10": "Add V2G capability; explore battery energy storage integration",
        },
    },
    "compact_urban": {
        "code": "compact_urban",
        "name": "Compact Urban",
        "icon": "📍",
        "fuel_dispensing_points": (4, 4),
        "ev_chargers": (2, 2),
        "charger_type": "AC Slow (7kW)",
        "retail_sqft": (200, 400),
        "amenities": ["Air & Water", "Digital Payment Kiosk"],
        "footprint_sqft": (5000, 10000),
        "capex_cr": 8.0,
        "description": "Small-footprint automated station for moderate-demand areas with basic fuel and minimal EV charging.",
        "transition_plan": {
            "year_3": "Upgrade 2 AC chargers to DC fast (60kW)",
            "year_5": "Evaluate demand growth; add convenience store if viable",
            "year_10": "Convert to hybrid format if demand crosses threshold",
        },
    },
    "hybrid_transition": {
        "code": "hybrid_transition",
        "name": "Hybrid Transition",
        "icon": "🔄",
        "fuel_dispensing_points": (6, 6),
        "ev_chargers": (0, 0),
        "charger_type": "Pre-wired for 6 EV chargers (install later)",
        "retail_sqft": (400, 600),
        "amenities": ["Convenience Store", "Air & Water", "Digital Payment Kiosk"],
        "footprint_sqft": (12000, 18000),
        "capex_cr": 12.0,
        "description": "Standard fuel station with electrical infrastructure pre-wired for future EV charger installation. Designed for cost-effective EV retrofit.",
        "transition_plan": {
            "year_3": "Install 4 DC fast chargers using pre-wired infrastructure",
            "year_5": "Add 2 more chargers; expand retail to 800 sqft",
            "year_10": "Evaluate full EV pivot based on regional adoption rates",
        },
    },
}


class FormatRecommender:
    """Recommends the optimal station format for a given location."""

    def recommend(self, location: dict) -> dict:
        """
        Apply the decision tree (priority order, first match wins).
        Returns the format dict enriched with reasoning.
        """
        tier = location.get("tier", "tier2")
        demand = float(location.get("demand", 50))
        competition = float(location.get("competition", 50))
        income = float(location.get("income", 50))
        ev = float(location.get("ev_readiness", 30))
        composite = location.get("composite_score", 50)

        # Rule 1: Large Highway Hub
        if tier == "highway" and demand > 55 and competition < 40:
            return self._build_result("large_highway_hub",
                f"Highway location with strong demand ({demand:.0f}/100) and low competition ({competition:.0f}/100) "
                f"supports a full-service highway hub with maximum throughput capacity.")

        # Rule 2: EV-Focused Station
        if ev > 65 and income > 70 and tier in ("metro", "emerging"):
            return self._build_result("ev_focused_station",
                f"High EV readiness ({ev:.0f}/100) in an affluent {tier} area ({income:.0f}/100 income) "
                f"makes this an ideal candidate for a primarily EV-focused station.")

        # Rule 3: Urban Full-Service
        if tier in ("metro", "emerging") and demand > 70 and income > 65:
            return self._build_result("urban_full_service",
                f"Strong urban demand ({demand:.0f}/100) with high purchasing power ({income:.0f}/100) "
                f"in a {tier} location supports a full-service urban station with balanced fuel and EV.")

        # Rule 4: Compact Urban
        if demand < 55 or (tier == "tier3" and composite < 45):
            return self._build_result("compact_urban",
                f"Moderate demand ({demand:.0f}/100) in a {tier} location suggests a compact format "
                f"with lower CAPEX and automated operations to optimize unit economics.")

        # Rule 5: Hybrid Transition (default)
        return self._build_result("hybrid_transition",
            f"Balanced profile across pillars in a {tier} location. A hybrid station with pre-wired "
            f"EV infrastructure allows cost-effective conversion as the market evolves.")

    def _build_result(self, format_code: str, reasoning: str) -> dict:
        fmt = dict(FORMATS[format_code])
        fmt["reasoning"] = reasoning
        return fmt

    def recommend_batch(self, locations: list) -> list:
        """Recommend format for a list of locations."""
        return [self.recommend(loc) for loc in locations]
