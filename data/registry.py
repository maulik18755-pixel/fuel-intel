"""
Data Source Registry — tracks all data sources with metadata, freshness, and provenance.
"""
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import pandas as pd


class DataSource(BaseModel):
    source_id: str
    source_name: str
    provider: str
    source_url: str
    api_available: bool = False
    api_endpoint: Optional[str] = None
    data_format: str = "CSV"
    update_frequency: str = "Annual"
    last_updated: datetime = datetime(2025, 1, 15)
    last_available_period: str = ""
    license: str = "Open Government Data"
    coverage: str = ""
    records_loaded: int = 0
    quality_notes: str = ""
    description: str = ""
    columns_used: list = []
    upload_instructions: str = ""
    seed_file: str = ""


FREQUENCY_DAYS = {
    "Real-time": 1,
    "Daily": 1,
    "Weekly": 7,
    "Monthly": 30,
    "Quarterly": 90,
    "Annual": 365,
    "Decennial": 3650,
    "Ad-hoc": 365,
}


class DataSourceRegistry:
    def __init__(self):
        self.sources: dict[str, DataSource] = {}
        self._register_all()

    def _register_all(self):
        self._register("CENSUS_2011",
            source_name="Census of India 2011", provider="Office of the Registrar General & Census Commissioner",
            source_url="https://censusindia.gov.in/census.website/data/census-tables",
            data_format="CSV", update_frequency="Decennial", last_available_period="2011",
            license="Open Government Data License - India",
            coverage="All India — District Level (640 districts)",
            description="Population, urbanization, household, literacy, and area data at district level. The foundational dataset for demand estimation and demographic scoring.",
            columns_used=["state", "district", "total_population", "urban_population", "area_sq_km", "population_density", "urban_pct", "literacy_rate"],
            upload_instructions="Download district-level population tables from censusindia.gov.in. Save as CSV with district, state, and population columns.",
            seed_file="census_districts.csv")

        self._register("VAHAN_VEHICLES",
            source_name="Vahan National Register — Vehicle Registrations", provider="Ministry of Road Transport and Highways",
            source_url="https://vahan.parivahan.gov.in/vahan4dashboard/",
            data_format="Excel", update_frequency="Monthly", last_available_period="Dec 2024",
            coverage="All India — State/UT Level",
            description="Registered vehicle counts by state, broken down by vehicle category (two-wheelers, cars, commercial, EVs). Key input for demand and EV readiness scoring.",
            columns_used=["state", "total_vehicles", "two_wheelers", "cars", "commercial", "ev_registered", "ev_share_pct"],
            upload_instructions="Visit vahan.parivahan.gov.in, select State-wise view, export to Excel. Save as .xlsx or CSV.",
            seed_file="vehicle_registrations.csv")

        self._register("PPAC_OUTLETS",
            source_name="PPAC — Retail Outlet Network", provider="Petroleum Planning & Analysis Cell, MoPNG",
            source_url="https://ppac.gov.in/",
            data_format="Excel/PDF", update_frequency="Annual", last_available_period="FY2024",
            coverage="All India — State Level by Oil Company",
            description="Count of fuel retail outlets by state and oil marketing company (IOCL, BPCL, HPCL, private). Used to compute competition density scores.",
            columns_used=["state", "total_outlets", "iocl", "bpcl", "hpcl", "reliance", "nayara", "shell", "outlets_per_lakh"],
            upload_instructions="Download from PPAC annual report or ready reckoner. Save the retail outlet table as CSV.",
            seed_file="fuel_stations_by_state.csv")

        self._register("PPAC_CONSUMPTION",
            source_name="PPAC — Petroleum Consumption", provider="Petroleum Planning & Analysis Cell, MoPNG",
            source_url="https://ppac.gov.in/consumption",
            data_format="Excel", update_frequency="Monthly", last_available_period="Nov 2024",
            coverage="All India — State Level",
            description="Monthly state-wise consumption of Motor Spirit (MS/petrol), High Speed Diesel (HSD), and LPG in thousand metric tonnes.",
            columns_used=["state", "ms_consumption_tmt", "hsd_consumption_tmt", "total_petroleum_tmt"],
            upload_instructions="Download monthly consumption data from PPAC website. Save as CSV with state and fuel type columns.",
            seed_file="fuel_consumption.csv")

        self._register("OPENCHARGE_MAP",
            source_name="OpenChargeMap — EV Charging Stations", provider="OpenChargeMap Community",
            source_url="https://openchargemap.org/site",
            api_available=True, api_endpoint="https://api.openchargemap.io/v3/poi/",
            data_format="JSON API", update_frequency="Real-time",
            last_available_period="Live",
            license="Creative Commons Attribution-ShareAlike",
            coverage="India — Point Level (lat/lng)",
            description="Community-maintained database of EV charging station locations with operator, connector type, and power details. The only live API source in the platform.",
            columns_used=["lat", "lng", "station_name", "operator", "connection_type", "power_kw", "status", "city", "state"],
            upload_instructions="Data refreshes automatically via API. For manual override, download from openchargemap.org and save as CSV.",
            seed_file="ev_charging_stations.csv")

        self._register("NHAI_HIGHWAYS",
            source_name="NHAI — National Highway Network", provider="National Highways Authority of India",
            source_url="https://nhai.gov.in/",
            data_format="GeoJSON/KML", update_frequency="Quarterly", last_available_period="Q3 2024",
            coverage="All India — Corridor Level",
            description="Major national highway corridors with length, lane count, and completion status. Used for infrastructure scoring and highway corridor identification.",
            columns_used=["corridor_name", "highway_number", "states", "total_length_km", "completed_km", "lanes", "status"],
            upload_instructions="Download highway project data from NHAI website or Bharatmala dashboard. Save corridor details as CSV.",
            seed_file="highway_corridors.csv")

        self._register("RBI_STATE_GDP",
            source_name="RBI — State Domestic Product (GSDP)", provider="Reserve Bank of India / MoSPI",
            source_url="https://data.rbi.org.in/",
            data_format="Excel", update_frequency="Annual", last_available_period="FY2023",
            coverage="All India — State/UT Level",
            description="Gross State Domestic Product at current and constant prices, and per capita income. Primary input for the income and spending power pillar.",
            columns_used=["state", "gsdp_current_cr", "per_capita_income_inr", "growth_rate_pct"],
            upload_instructions="Download GSDP tables from data.rbi.org.in or MoSPI. Save as Excel or CSV with state and income columns.",
            seed_file="state_gdp.csv")

        self._register("SMART_CITIES",
            source_name="Smart Cities Mission — City List & Progress", provider="Ministry of Housing and Urban Affairs",
            source_url="https://smartcities.gov.in/",
            data_format="Static List", update_frequency="Ad-hoc", last_available_period="2024",
            coverage="100 Smart Cities",
            description="List of 100 Smart Cities with investment commitments and project completion status. Used as a growth trajectory signal.",
            columns_used=["city", "state", "year_selected", "total_investment_cr", "completion_pct"],
            upload_instructions="Download the city-wise progress report from smartcities.gov.in. Save as CSV.",
            seed_file="smart_cities.csv")

        self._register("BHARATMALA",
            source_name="Bharatmala Pariyojana — Highway Development", provider="Ministry of Road Transport / NHAI",
            source_url="https://bharatmala.nhai.gov.in/",
            data_format="PDF/Excel", update_frequency="Quarterly", last_available_period="Q3 2024",
            coverage="All India — Corridor Level",
            description="Phase-wise highway development under Bharatmala with corridor details and completion timelines. Growth trajectory signal for highway locations.",
            columns_used=["corridor_name", "states", "total_km", "completed_km", "expected_completion"],
            upload_instructions="Download Bharatmala progress reports from the official portal. Save corridor data as CSV.",
            seed_file="highway_corridors.csv")

        self._register("BEE_EV_CHARGING",
            source_name="BEE — EV Charging Infrastructure Guidelines", provider="Bureau of Energy Efficiency, Ministry of Power",
            source_url="https://beeindia.gov.in/",
            data_format="PDF/Excel", update_frequency="Quarterly", last_available_period="Q3 2024",
            coverage="All India — State Level",
            description="Public EV charging infrastructure guidelines and registered charging points. Supplements OpenChargeMap data for EV readiness scoring.",
            columns_used=["state", "public_chargers", "dc_fast_chargers", "operators"],
            upload_instructions="Download EV charging station registry from BEE or Ministry of Power. Save as CSV.",
            seed_file="ev_charging_stations.csv")

    def _register(self, source_id: str, **kwargs):
        self.sources[source_id] = DataSource(source_id=source_id, **kwargs)

    def get_source(self, source_id: str) -> DataSource:
        return self.sources.get(source_id)

    def get_all_sources(self) -> list:
        return list(self.sources.values())

    def update_freshness(self, source_id: str, records: int, timestamp: datetime = None):
        if source_id in self.sources:
            self.sources[source_id].records_loaded = records
            self.sources[source_id].last_updated = timestamp or datetime.now()

    def get_freshness_status(self, source_id: str) -> str:
        src = self.sources.get(source_id)
        if not src:
            return "unknown"
        freq_days = FREQUENCY_DAYS.get(src.update_frequency, 365)
        age = (datetime.now() - src.last_updated).days
        if age <= freq_days:
            return "fresh"
        elif age <= freq_days * 1.5:
            return "stale"
        else:
            return "outdated"

    def get_freshness_icon(self, source_id: str) -> str:
        status = self.get_freshness_status(source_id)
        return {"fresh": "🟢", "stale": "🟡", "outdated": "🔴"}.get(status, "⚪")

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for s in self.sources.values():
            rows.append({
                "Source": s.source_name,
                "Provider": s.provider,
                "Format": s.data_format,
                "Frequency": s.update_frequency,
                "Last Updated": s.last_updated.strftime("%Y-%m-%d"),
                "Freshness": self.get_freshness_icon(s.source_id),
                "Records": s.records_loaded,
                "Coverage": s.coverage,
                "API": "✅" if s.api_available else "—",
            })
        return pd.DataFrame(rows)
