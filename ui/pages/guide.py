"""User Guide — how to update data, upload files, and interpret results."""
import streamlit as st
import pandas as pd


UPLOAD_SOURCES = {
    "VAHAN_VEHICLES": {"label": "Vehicle Registrations (Vahan)", "template_cols": "state,total_vehicles,two_wheelers,cars,commercial,three_wheelers,ev_registered,ev_share_pct,data_period"},
    "PPAC_OUTLETS": {"label": "Fuel Stations (PPAC)", "template_cols": "state,total_outlets,iocl,bpcl,hpcl,reliance,nayara,shell,others,outlets_per_lakh"},
    "PPAC_CONSUMPTION": {"label": "Fuel Consumption (PPAC)", "template_cols": "state,ms_consumption_tmt,hsd_consumption_tmt,total_petroleum_tmt,data_period"},
    "CENSUS_2011": {"label": "Census / Population Data", "template_cols": "state,district,total_population,urban_population,area_sq_km,population_density,urban_pct,literacy_rate"},
    "RBI_STATE_GDP": {"label": "State GDP (RBI)", "template_cols": "state,gsdp_current_cr,per_capita_income_inr,growth_rate_pct,year"},
    "OPENCHARGE_MAP": {"label": "EV Charging Stations", "template_cols": "name,lat,lng,city,state,operator,connection_type,power_kw,num_points,status"},
    "SMART_CITIES": {"label": "Smart Cities", "template_cols": "city,state,year_selected,total_investment_cr,completion_pct,category"},
    "NHAI_HIGHWAYS": {"label": "Highway Corridors", "template_cols": "corridor_name,highway_number,states,total_length_km,completed_km,lanes,status,bharatmala_phase"},
    "SCORED_LOCATIONS": {"label": "New Candidate Locations", "template_cols": "name,lat,lng,state,tier,demand,competition,income,ev_readiness,infrastructure,growth_trajectory"},
}


def render(registry, pipeline=None):
    st.title("User Guide")
    st.caption("How to update data sources, upload fresh datasets, and interpret results")

    # --- Quick Start ---
    st.subheader("Quick Start")
    st.markdown("""
    This platform analyzes potential fuel retail and EV charging locations across India by combining
    **10 public data sources** to score locations on **6 dimensions** and recommend the optimal
    station format and investment priority.

    **Key pages:**
    - **Executive Summary** — Start here. See the headline insights and top investment targets.
    - **Heat Map** — Visual map with filters to explore locations geographically.
    - **Location Deep Dive** — Select any location for full financial projection and format recommendation.
    - **Scenario Comparison** — Test how different strategic priorities change rankings.
    - **Investment Matrix** — Capital allocation view with fast-track/deprioritize classification.
    - **Architecture** — All data sources, assumptions, and methodology in full detail.
    """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- How to Update Data ---
    st.subheader("How to Update Each Data Source")

    with st.expander("📊 Vehicle Registration Data (Vahan) — Update Monthly"):
        st.markdown("""
        **Where to download:** [vahan.parivahan.gov.in](https://vahan.parivahan.gov.in/vahan4dashboard/)

        **Steps:**
        1. Visit the Vahan dashboard link above
        2. Select **"State-wise"** view from the top menu
        3. Set vehicle category to **"All"**
        4. Click **"Export to Excel"** (top right corner)
        5. Save the file as `vehicle_registrations_YYYYMMDD.xlsx`
        6. Upload it below using the upload widget

        **Required columns:** state, total_vehicles, two_wheelers, cars, commercial, ev_registered, ev_share_pct
        """)

    with st.expander("⛽ Fuel Station Data (PPAC) — Update Annually"):
        st.markdown("""
        **Where to download:** [ppac.gov.in](https://ppac.gov.in/)

        **Steps:**
        1. Visit PPAC website → Reports → Ready Reckoner
        2. Download the latest annual report
        3. Find Table: "State-wise Retail Outlets" — copy to a spreadsheet
        4. Save as CSV with required columns
        5. Upload below

        **Required columns:** state, total_outlets, iocl, bpcl, hpcl, reliance, outlets_per_lakh
        """)

    with st.expander("🔋 EV Charging Stations — Auto-refreshes via API"):
        st.markdown("""
        **Source:** [OpenChargeMap](https://openchargemap.org/site)

        This is the only live API source. Data refreshes automatically when available.
        For manual override, download from OpenChargeMap website → Export India data → Upload as CSV.

        **Required columns:** name, lat, lng, city, state, operator, connection_type, power_kw, num_points, status
        """)

    with st.expander("💰 State GDP Data (RBI) — Update Annually"):
        st.markdown("""
        **Where to download:** [data.rbi.org.in](https://data.rbi.org.in/)

        **Steps:**
        1. Visit RBI Data → Database on Indian Economy
        2. Search for "State Domestic Product"
        3. Download GSDP and per capita income tables
        4. Format as CSV with required columns
        5. Upload below

        **Required columns:** state, gsdp_current_cr, per_capita_income_inr, growth_rate_pct
        """)

    with st.expander("📍 Add New Candidate Locations"):
        st.markdown("""
        You can add new locations to the analysis by uploading a CSV with location details and pillar scores.

        **Required columns:** name, lat, lng, state, tier, demand, competition, income, ev_readiness, infrastructure, growth_trajectory

        **Tier values:** metro, tier2, tier3, highway, emerging

        **Pillar scores:** 0-100 for each pillar. If unknown, use 50 as default.
        """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Upload Widget ---
    st.subheader("Upload Data")
    source_options = {v["label"]: k for k, v in UPLOAD_SOURCES.items()}
    selected_label = st.selectbox("Select data source type", list(source_options.keys()))
    source_id = source_options[selected_label]

    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith((".xlsx", ".xls")):
                preview_df = pd.read_excel(uploaded_file)
            else:
                preview_df = pd.read_csv(uploaded_file, comment="#")

            st.markdown("**Preview (first 10 rows):**")
            st.dataframe(preview_df.head(10), use_container_width=True, hide_index=True)

            required = UPLOAD_SOURCES[source_id]["template_cols"].split(",")
            found = [c for c in required if c in preview_df.columns]
            missing = [c for c in required if c not in preview_df.columns]

            if missing:
                st.error(f"❌ Missing required columns: **{', '.join(missing)}**")
            else:
                st.success(f"✅ All required columns found. {len(preview_df)} rows detected.")

            if st.button("Load & Refresh Scores", disabled=len(missing) > 0):
                st.info("In production, this would reload the data pipeline and recalculate all scores. "
                        "For now, please re-deploy after adding the file to data/seed/.")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Download Templates ---
    st.subheader("Download Data Templates")
    st.caption("Use these templates to format your data before uploading.")

    cols = st.columns(3)
    for i, (source_id, info) in enumerate(UPLOAD_SOURCES.items()):
        with cols[i % 3]:
            template_content = info["template_cols"] + "\n"
            template_content += ",".join(["example"] * len(info["template_cols"].split(","))) + "\n"
            st.download_button(
                f"📥 {info['label']}",
                template_content,
                f"template_{source_id.lower()}.csv",
                "text/csv",
                use_container_width=True,
            )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Interpreting Results ---
    st.subheader("Interpreting Results")
    st.markdown("""
    **Composite Score (0-100):** Weighted combination of 6 pillar scores. Higher is better.
    - **≥70:** High Potential — strong across multiple dimensions, likely profitable
    - **45-69:** Moderate — some strengths but also gaps that need assessment
    - **<45:** Low Potential — significant challenges, may not be viable without market changes

    **Format Recommendation:** The platform suggests one of 5 station types based on location characteristics.
    The format determines CAPEX, operational model, and long-term transition strategy.

    **15-Year NPV:** Net present value of projected cash flows at 12% discount rate. Positive = value-creating.

    **Payback Period:** Years until cumulative cash flows turn positive. <5 years = excellent, 5-8 = good, >8 = cautious.

    **Action Classification:**
    - 🟢 **Fast-Track:** Score ≥80, payback ≤5 years. Move immediately.
    - 🟡 **Detailed Feasibility:** Score ≥65, payback ≤8 years. Worth investigating.
    - 🔵 **Monitor & Evaluate:** Score ≥45. Watch for improvement triggers.
    - ⚪ **Deprioritize:** Score <45. Revisit in 2-3 years.
    """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- FAQ ---
    st.subheader("Frequently Asked Questions")
    faqs = [
        ("How often should I update the data?", "Monthly for vehicle registrations and fuel consumption. Quarterly for EV charging, highways, and smart cities. Annually for census and GDP. The Architecture tab shows freshness status for each source."),
        ("Can I add new candidate locations?", "Yes. Upload a CSV with name, lat, lng, state, tier, and pillar scores (0-100). Use the 'New Candidate Locations' template above."),
        ("What if a data source is unavailable?", "The platform uses pre-loaded seed data as fallback. Scores will still compute but may be less accurate. The Architecture tab flags stale sources with 🟡 or 🔴 indicators."),
        ("How do I change the scoring weights?", "Use the Scenario Comparison page to test different weight configurations (EV-First, Fuel Maximizer, Growth Corridor) or create custom weights."),
        ("Can I export the results?", "Yes. Every page has a download button for CSV export. The Executive Summary provides a full analysis report."),
        ("What does 'Not viable' mean for payback?", "It means the location's projected cash flows don't turn positive within 15 years under current assumptions. Consider a smaller format or different assumptions."),
        ("How reliable are the financial projections?", "They are estimates based on documented assumptions (see Architecture tab). The Sensitivity Analysis on the Deep Dive page shows how results change when assumptions shift ±20%."),
        ("What is the competition score inversion?", "A raw competition score of 20 means LOW competition (few existing stations). During scoring, this is inverted to 80 (high opportunity). Low competition = high opportunity."),
    ]
    for q, a in faqs:
        with st.expander(q):
            st.markdown(a)
