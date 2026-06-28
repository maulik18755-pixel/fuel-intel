"""
Fuel & EV Location Intelligence Platform
Main Streamlit entry point.
"""
import streamlit as st
from ui.theme import BRAND_CSS
from data.registry import DataSourceRegistry
from data.ingestion import DataPipeline
from core.scoring_engine import ScoringEngine
from core.format_recommender import FormatRecommender
from core.profitability_model import ProfitabilityModel
from config.settings import Settings

st.set_page_config(
    page_title="Fuel & EV Location Intelligence",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(BRAND_CSS, unsafe_allow_html=True)


# ── Cached initialization ────────────────────────────────────────────────────
@st.cache_resource
def init_registry():
    return DataSourceRegistry()


@st.cache_data(ttl=3600)
def load_data(_registry):
    pipeline = DataPipeline(_registry)
    all_data = pipeline.load_all()
    master_df = pipeline.build_master_table()
    return pipeline, all_data, master_df


registry = init_registry()
pipeline, all_data, master_df = load_data(registry)
scoring_engine = ScoringEngine()
format_recommender = FormatRecommender()
profitability_model = ProfitabilityModel()


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⛽ Fuel & EV Intel")
    page = st.radio(
        "Navigate",
        [
            "📊 Executive Summary",
            "🗺️ Location Heat Map",
            "🔍 Location Deep Dive",
            "⚖️ Scenario Comparison",
            "📐 Investment Matrix",
            "🏗️ Architecture & Data",
            "📖 User Guide",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"Locations: {len(master_df)}")
    st.caption(f"Data Sources: {len(registry.sources)} active")
    st.caption("v1.1.0 · Integrated Downstream Company")


# ── Page routing ─────────────────────────────────────────────────────────────
if page == "📊 Executive Summary":
    from ui.pages.executive_summary import render
    render(master_df, registry)

elif page == "🗺️ Location Heat Map":
    from ui.pages.heat_map import render
    render(master_df)

elif page == "🔍 Location Deep Dive":
    from ui.pages.location_deep_dive import render
    render(master_df, profitability_model, format_recommender)

elif page == "⚖️ Scenario Comparison":
    from ui.pages.scenario_comparison import render
    render(master_df, scoring_engine)

elif page == "📐 Investment Matrix":
    from ui.pages.investment_matrix import render
    render(master_df)

elif page == "🏗️ Architecture & Data":
    from ui.pages.architecture import render
    render(registry, pipeline)

elif page == "📖 User Guide":
    from ui.pages.guide import render
    render(registry, pipeline)
