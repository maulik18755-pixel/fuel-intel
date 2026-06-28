"""Architecture & Data Sources — full transparency on data, methodology, and assumptions."""
import streamlit as st
import pandas as pd
from config.assumptions import MODEL_ASSUMPTIONS, ASSUMPTION_CATEGORIES
from ui.theme import insight_box


def render(registry, pipeline):
    st.title("Architecture & Data Sources")
    st.caption("Full transparency on data provenance, methodology, and model assumptions")

    # --- 1. System Overview ---
    st.markdown(insight_box(
        "System Architecture",
        "The platform ingests data from <b>10 sources</b> (1 live API, 9 manual upload/seed) → "
        "Data Pipeline validates, cleans, and enriches each location with state and district-level context → "
        "Scoring Engine computes Location Attractiveness Score across 6 weighted pillars → "
        "Format Recommender selects optimal station type via rule-based decision tree → "
        "Profitability Model projects 15-year cash flows with NPV, IRR, and payback analysis."
    ), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 2. Data Source Inventory ---
    st.subheader("Data Source Inventory")
    source_df = registry.to_dataframe()
    st.dataframe(source_df, use_container_width=True, hide_index=True)

    st.markdown("")
    for src in registry.get_all_sources():
        icon = registry.get_freshness_icon(src.source_id)
        status = registry.get_freshness_status(src.source_id)
        with st.expander(f"{icon} {src.source_name} — {status.upper()}"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Provider:** {src.provider}")
                st.markdown(f"**Format:** {src.data_format}")
                st.markdown(f"**Update Frequency:** {src.update_frequency}")
                st.markdown(f"**Records Loaded:** {src.records_loaded:,}")
                st.markdown(f"**License:** {src.license}")
            with c2:
                st.markdown(f"**Last Updated:** {src.last_updated.strftime('%Y-%m-%d')}")
                st.markdown(f"**Latest Period:** {src.last_available_period}")
                st.markdown(f"**Coverage:** {src.coverage}")
                st.markdown(f"**API Available:** {'Yes' if src.api_available else 'No'}")
                if src.source_url:
                    st.markdown(f"[🔗 Source URL]({src.source_url})")
            st.markdown(f"**Description:** {src.description}")
            st.markdown(f"**Columns Used:** {', '.join(src.columns_used)}")
            if src.quality_notes:
                st.warning(f"Quality Note: {src.quality_notes}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 3. Model Assumptions ---
    st.subheader("Model Assumptions")
    st.caption("Every assumption is documented, sourced, and rated for sensitivity impact.")

    for category in ASSUMPTION_CATEGORIES:
        cat_assumptions = [a for a in MODEL_ASSUMPTIONS if a["category"] == category]
        if not cat_assumptions:
            continue
        st.markdown(f"#### {category}")
        for a in cat_assumptions:
            sens_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(a["sensitivity"], "⚪")
            st.markdown(f"**{a['id']}** {sens_color} {a['assumption']}")
            st.caption(f"Value: {a['value']} · Source: {a['source']} · Sensitivity: {a['sensitivity']}")
        st.markdown("")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 4. Scoring Methodology ---
    st.subheader("Scoring Methodology")
    st.markdown("""
    **Six Pillars** — Each location is scored 0-100 on six dimensions:

    **Demand Intensity** (30% default weight) — Vehicle density, traffic volume, fuel consumption patterns. Higher vehicle registrations and highway traffic yield higher scores.

    **Competition Gap** (20%) — Inverse of existing fuel station density. Fewer stations per lakh population = higher opportunity. This pillar is **inverted** during scoring: raw competition of 20 (low competition) becomes a pillar score of 80 (high opportunity).

    **Income & Spending Power** (15%) — State GDP per capita and consumption expenditure as proxy for willingness to pay for premium services and EV adoption.

    **EV Readiness** (15%) — Current EV registration share, charging infrastructure density, and state EV policy strength. Leading indicator of future revenue mix.

    **Infrastructure Quality** (10%) — Road quality (NH/SH classification), grid reliability, land availability. Highway locations with multi-lane access score higher.

    **Growth Trajectory** (10%) — Smart City designation, upcoming expressway projects, industrial corridor proximity, and population growth rate. Forward-looking signal.

    **Composite Score** = Weighted sum of all pillar scores, clamped to 0-100.

    **Score Tiers:** High Potential (≥70) → Moderate (≥45) → Low Potential (<45)
    """)

    st.markdown("""
    **Format Decision Tree** (priority order, first match wins):
    1. **Large Highway Hub** — Highway tier + demand >55 + competition <40
    2. **EV-Focused Station** — EV readiness >65 + income >70 + metro/emerging tier
    3. **Urban Full-Service** — Metro/emerging + demand >70 + income >65
    4. **Compact Urban** — Demand <55 or low-scoring tier-3
    5. **Hybrid Transition** — Default for balanced profiles
    """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 5. Data Quality ---
    st.subheader("Data Quality Dashboard")
    total_records = sum(s.records_loaded for s in registry.get_all_sources())
    st.metric("Total Records Across All Sources", f"{total_records:,}")

    if pipeline.warnings:
        st.warning(f"**{len(pipeline.warnings)} warnings during data loading:**")
        for w in pipeline.warnings:
            st.caption(f"⚠️ {w}")
    else:
        st.success("All data sources loaded without warnings.")
