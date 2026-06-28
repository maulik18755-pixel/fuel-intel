"""
Data Pipeline — loads all seed/uploaded data, enriches locations, runs scoring.
"""
import os
import pandas as pd
from datetime import datetime
from data.registry import DataSourceRegistry
from core.scoring_engine import ScoringEngine, load_locations_from_csv
from core.format_recommender import FormatRecommender
from core.profitability_model import ProfitabilityModel
from config.settings import Settings

BASE_SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed")


def _load_csv(filename, seed_dir=None):
    path = os.path.join(seed_dir or BASE_SEED_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, comment="#")


class DataPipeline:
    def __init__(self, registry=None):
        self.registry = registry or DataSourceRegistry()
        self.data = {}
        self.warnings = []
        self.settings = Settings()

    def load_all(self):
        loaders = {
            "CENSUS_2011": "census_districts.csv",
            "VAHAN_VEHICLES": "vehicle_registrations.csv",
            "PPAC_OUTLETS": "fuel_stations_by_state.csv",
            "PPAC_CONSUMPTION": "fuel_consumption.csv",
            "OPENCHARGE_MAP": "ev_charging_stations.csv",
            "NHAI_HIGHWAYS": "highway_corridors.csv",
            "RBI_STATE_GDP": "state_gdp.csv",
            "SMART_CITIES": "smart_cities.csv",
            "BHARATMALA": "highway_corridors.csv",
            "BEE_EV_CHARGING": "ev_charging_stations.csv",
        }
        for source_id, filename in loaders.items():
            try:
                df = _load_csv(filename)
                if not df.empty:
                    self.data[source_id] = df
                    self.registry.update_freshness(source_id, len(df))
                else:
                    self.warnings.append(f"Empty dataset for {source_id}")
            except Exception as e:
                self.warnings.append(f"Failed to load {source_id}: {e}")
                self.data[source_id] = pd.DataFrame()
        return self.data

    def load_uploaded_file(self, source_id, filepath):
        source = self.registry.get_source(source_id)
        if not source:
            return False, f"Unknown source: {source_id}", pd.DataFrame()
        try:
            if filepath.endswith((".xlsx", ".xls")):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath, comment="#")
            if df.empty:
                return False, "File is empty.", df
            required = source.columns_used
            missing = [c for c in required if c not in df.columns]
            if missing:
                return False, f"Missing required columns: {', '.join(missing)}", df
            self.data[source_id] = df
            self.registry.update_freshness(source_id, len(df))
            return True, f"Loaded {len(df)} records for {source.source_name}.", df
        except Exception as e:
            return False, f"Error parsing file: {e}", pd.DataFrame()

    def build_master_table(self):
        locations = load_locations_from_csv(os.path.join(BASE_SEED_DIR, "scored_locations.csv"))
        vahan = self.data.get("VAHAN_VEHICLES", pd.DataFrame())
        gdp = self.data.get("RBI_STATE_GDP", pd.DataFrame())
        outlets = self.data.get("PPAC_OUTLETS", pd.DataFrame())
        smart = self.data.get("SMART_CITIES", pd.DataFrame())
        ev_stations = self.data.get("OPENCHARGE_MAP", pd.DataFrame())

        for loc in locations:
            state = loc.get("state", "")
            state_key = state.split()[0] if state else ""

            if not vahan.empty and "state" in vahan.columns:
                row = vahan[vahan["state"].str.contains(state_key, case=False, na=False)]
                if not row.empty:
                    r = row.iloc[0]
                    loc["total_vehicles"] = int(r.get("total_vehicles", 0))
                    loc["ev_registered"] = int(r.get("ev_registered", 0))
                    loc["ev_share_pct"] = float(r.get("ev_share_pct", 0))

            if not gdp.empty and "state" in gdp.columns:
                row = gdp[gdp["state"].str.contains(state_key, case=False, na=False)]
                if not row.empty:
                    loc["per_capita_income"] = int(row.iloc[0].get("per_capita_income_inr", 0))

            if not outlets.empty and "state" in outlets.columns:
                row = outlets[outlets["state"].str.contains(state_key, case=False, na=False)]
                if not row.empty:
                    loc["total_fuel_outlets"] = int(row.iloc[0].get("total_outlets", 0))
                    loc["outlets_per_lakh"] = float(row.iloc[0].get("outlets_per_lakh", 0))

            loc["smart_city"] = False
            if not smart.empty and "city" in smart.columns:
                nm = loc.get("name", "").lower()
                for _, sc in smart.iterrows():
                    if str(sc.get("city", "")).lower() in nm:
                        loc["smart_city"] = True
                        break

            loc["nearby_ev_chargers"] = 0
            if not ev_stations.empty and "lat" in ev_stations.columns:
                lat, lng = float(loc.get("lat", 0)), float(loc.get("lng", 0))
                for _, ev in ev_stations.iterrows():
                    dlat = abs(float(ev.get("lat", 0)) - lat)
                    dlng = abs(float(ev.get("lng", 0)) - lng)
                    if dlat < 0.25 and dlng < 0.25:
                        loc["nearby_ev_chargers"] += int(ev.get("num_points", 1))

        engine = ScoringEngine()
        scored_df = engine.score_batch(locations)
        recommender = FormatRecommender()
        profitability = ProfitabilityModel()

        fmt_names, fmt_codes, fmt_icons, npvs, irrs = [], [], [], [], []
        paybacks, viables, reasonings, peaks, crossovers = [], [], [], [], []

        for _, row in scored_df.iterrows():
            loc_dict = row.to_dict()
            fmt = recommender.recommend(loc_dict)
            profit = profitability.project_cash_flows(loc_dict, fmt)
            fmt_names.append(fmt["name"])
            fmt_codes.append(fmt["code"])
            fmt_icons.append(fmt["icon"])
            npvs.append(profit["npv_cr"])
            irrs.append(profit["irr_pct"])
            paybacks.append(profit["payback_years"])
            viables.append(profit["viable"])
            reasonings.append(fmt["reasoning"])
            peaks.append(profit["peak_annual_revenue_cr"])
            crossovers.append(profit.get("ev_crossover_year"))

        scored_df["format_name"] = fmt_names
        scored_df["format_code"] = fmt_codes
        scored_df["format_icon"] = fmt_icons
        scored_df["npv_cr"] = npvs
        scored_df["irr_pct"] = irrs
        scored_df["payback_years"] = paybacks
        scored_df["viable"] = viables
        scored_df["format_reasoning"] = reasonings
        scored_df["peak_revenue_cr"] = peaks
        scored_df["ev_crossover_year"] = crossovers

        def get_action(r):
            if r["composite_score"] >= 80 and r["payback_years"] <= 5:
                return "🟢 Fast-Track"
            elif r["composite_score"] >= 65 and r["payback_years"] <= 8:
                return "🟡 Detailed Feasibility"
            elif r["composite_score"] >= 45:
                return "🔵 Monitor & Evaluate"
            return "⚪ Deprioritize"

        scored_df["action"] = scored_df.apply(get_action, axis=1)
        return scored_df
