"""
15-Year Profitability Model.
Projects cash flows, computes NPV, IRR, and payback for each location × format combination.
"""
import math
import numpy as np
from config.settings import Settings


class ProfitabilityModel:
    def __init__(self, settings: Settings = None):
        self.s = settings or Settings()

    def project_cash_flows(self, location: dict, format_spec: dict) -> dict:
        """
        Build a 15-year cash flow projection for a location + format combination.
        Returns dict with annual_cash_flows, npv, irr, payback_years, and summary metrics.
        """
        s = self.s
        tier = location.get("tier", "tier2")
        demand = float(location.get("demand", 50))
        ev_score = float(location.get("ev_readiness", 30))

        # --- Extract format specs ---
        fuel_points_mid = sum(format_spec.get("fuel_dispensing_points", (4, 6))) / 2
        ev_charger_range = format_spec.get("ev_chargers", (0, 0))
        ev_chargers = sum(ev_charger_range) / 2
        retail_sqft = sum(format_spec.get("retail_sqft", (400, 600))) / 2
        capex = format_spec.get("capex_cr", 12.0)

        # --- Base calculations ---
        daily_vehicles = (demand / 100) * 1500
        car_pct, comm_pct = s.get_vehicle_mix(tier)
        fuel_prob = s.get_fueling_prob(tier)
        avg_litres = car_pct * s.avg_fill_car_litres + comm_pct * s.avg_fill_commercial_litres
        capacity_factor = fuel_points_mid / 6  # 6 dispensers as reference baseline

        # --- Fixed annual costs ---
        land_lease_cr = s.get_land_lease(tier) / 100  # Lakhs to Cr
        staff_count, staff_per_person_l = s.get_staff_cost(tier)
        staff_cost_cr = (staff_count * staff_per_person_l) / 100  # Lakhs to Cr
        opex_cr = s.opex_pct_of_capex * capex
        utilities_cr = s.utilities_base_cr + s.utilities_per_charger_cr * ev_chargers

        # --- Build annual cash flows ---
        annual_flows = []
        cumulative_cf = -capex
        all_net_cfs = [-capex]

        for year in range(1, s.npv_horizon_years + 1):
            # Fuel revenue with decline
            if year >= s.fuel_decline_start_year:
                fuel_decline = (1 - s.fuel_decline_rate_annual) ** (year - s.fuel_decline_start_year)
            else:
                fuel_decline = 1.0
            fuel_revenue = (daily_vehicles * fuel_prob * avg_litres * s.fuel_margin_per_litre * 365 * capacity_factor * fuel_decline) / 1e7  # ₹ to Cr

            # EV revenue with S-curve growth
            if ev_chargers > 0:
                t = min(year, 10) / 10  # 0 to 1 over 10 years
                sessions = s.ev_sessions_per_charger_day_y1 + (s.ev_sessions_per_charger_day_y10 - s.ev_sessions_per_charger_day_y1) * (t ** 1.5)
                ev_base_factor = (ev_score / 100) * 0.5 + 0.5  # Scale by EV readiness
                ev_revenue = (ev_chargers * sessions * s.avg_kwh_per_session * s.ev_margin_per_kwh * 365 * ev_base_factor) / 1e7
            else:
                ev_revenue = 0
                sessions = 0

            # Retail revenue with inflation growth
            retail_revenue = (retail_sqft * s.convenience_revenue_per_sqft_annual * ((1 + s.retail_revenue_growth_annual) ** (year - 1))) / 1e7

            # Ancillary
            ancillary_revenue = s.ancillary_revenue_pct_of_fuel * fuel_revenue

            total_revenue = fuel_revenue + ev_revenue + retail_revenue + ancillary_revenue

            # Costs
            year_utilities = utilities_cr
            year_extra = 0
            if year == s.ev_charger_replacement_year and ev_chargers > 0:
                year_extra = s.ev_charger_replacement_pct * ev_chargers * s.ev_charger_cost_cr_each

            total_cost = opex_cr + land_lease_cr + staff_cost_cr + year_utilities + year_extra

            net_cf = total_revenue - total_cost
            cumulative_cf += net_cf
            discounted_cf = net_cf / ((1 + s.discount_rate) ** year)

            annual_flows.append({
                "year": year,
                "fuel_revenue_cr": round(fuel_revenue, 3),
                "ev_revenue_cr": round(ev_revenue, 3),
                "retail_revenue_cr": round(retail_revenue, 3),
                "ancillary_revenue_cr": round(ancillary_revenue, 3),
                "total_revenue_cr": round(total_revenue, 3),
                "opex_cr": round(opex_cr, 3),
                "land_lease_cr": round(land_lease_cr, 3),
                "staff_cost_cr": round(staff_cost_cr, 3),
                "utilities_cr": round(year_utilities, 3),
                "replacement_cr": round(year_extra, 3),
                "total_cost_cr": round(total_cost + year_extra, 3),
                "net_cash_flow_cr": round(net_cf, 3),
                "cumulative_cf_cr": round(cumulative_cf, 3),
                "discounted_cf_cr": round(discounted_cf, 3),
            })
            all_net_cfs.append(net_cf)

        # --- Summary metrics ---
        npv = sum(f["discounted_cf_cr"] for f in annual_flows) - capex
        npv = round(npv, 1)

        # Payback period
        payback = 99.0
        cum = -capex
        for f in annual_flows:
            prev_cum = cum
            cum += f["net_cash_flow_cr"]
            if cum >= 0 and prev_cum < 0:
                if f["net_cash_flow_cr"] > 0:
                    fraction = -prev_cum / f["net_cash_flow_cr"]
                else:
                    fraction = 0
                payback = round(f["year"] - 1 + fraction, 1)
                break

        # IRR via numpy
        try:
            irr = float(np.irr(all_net_cfs)) * 100 if hasattr(np, 'irr') else self._compute_irr(all_net_cfs)
        except Exception:
            irr = self._compute_irr(all_net_cfs)
        irr = round(irr, 1)

        # Revenue CAGR
        rev_y1 = annual_flows[0]["total_revenue_cr"]
        rev_y15 = annual_flows[-1]["total_revenue_cr"]
        if rev_y1 > 0:
            cagr = ((rev_y15 / rev_y1) ** (1 / 14) - 1) * 100
        else:
            cagr = 0
        cagr = round(cagr, 1)

        # EV crossover year
        ev_crossover = None
        for f in annual_flows:
            if f["ev_revenue_cr"] > f["fuel_revenue_cr"] and f["ev_revenue_cr"] > 0:
                ev_crossover = f["year"]
                break

        peak_revenue = max(f["total_revenue_cr"] for f in annual_flows)

        return {
            "annual_cash_flows": annual_flows,
            "npv_cr": npv,
            "irr_pct": irr,
            "payback_years": payback,
            "total_investment_cr": capex,
            "peak_annual_revenue_cr": round(peak_revenue, 2),
            "revenue_cagr_pct": cagr,
            "ev_crossover_year": ev_crossover,
            "viable": payback <= s.npv_horizon_years,
        }

    def _compute_irr(self, cash_flows: list, guess: float = 0.1) -> float:
        """Compute IRR using Newton's method with divergence guard."""
        rate = guess
        for _ in range(200):
            npv_val = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
            dnpv = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
            if abs(dnpv) < 1e-12:
                break
            new_rate = rate - npv_val / dnpv
            # Guard: clamp rate to prevent divergence
            if new_rate < -0.5 or new_rate > 5.0:
                return rate * 100
            if abs(new_rate - rate) < 1e-7:
                rate = new_rate
                break
            rate = new_rate
        return max(-50, min(200, rate * 100))
