"""
Data Pipeline — loads data, generates candidates, auto-scores, runs format+profitability.
"""
import os
import pandas as pd
from datetime import datetime
from data.registry import DataSourceRegistry
from core.scoring_engine import ScoringEngine
from core.format_recommender import FormatRecommender
from core.profitability_model import ProfitabilityModel
from core.auto_scorer import AutoScorer
from core.candidate_generator import CandidateGenerator
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

    def build_master_table(self) -> pd.DataFrame:
        """
        Generate candidates → auto-score from data → format → profitability.
        This replaces the old approach of reading manually-scored locations.
        """
        # Step 1: Generate candidate locations from district data + highways
        generator = CandidateGenerator()
        census = self.data.get("CENSUS_2011", pd.DataFrame())
        candidates = generator.generate_all(census)

        # Step 2: Auto-score from actual data
        scorer = AutoScorer(
            state_vehicles=self.data.get("VAHAN_VEHICLES", pd.DataFrame()),
            state_gdp=self.data.get("RBI_STATE_GDP", pd.DataFrame()),
            state_outlets=self.data.get("PPAC_OUTLETS", pd.DataFrame()),
            state_consumption=self.data.get("PPAC_CONSUMPTION", pd.DataFrame()),
            census=census,
            ev_stations=self.data.get("OPENCHARGE_MAP", pd.DataFrame()),
            smart_cities=self.data.get("SMART_CITIES", pd.DataFrame()),
            highways=self.data.get("NHAI_HIGHWAYS", pd.DataFrame()),
        )
        scored_candidates = scorer.score_candidates(candidates)

        # Step 3: Compute composite score using the scoring engine
        engine = ScoringEngine()
        locations = scored_candidates.to_dict("records")
        scored_df = engine.score_batch(locations)

        # Step 4: Format recommendation + profitability for each
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
