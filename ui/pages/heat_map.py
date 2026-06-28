"""Interactive Heat Map — India map with official boundaries and scored locations."""
import os
import json
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from utils.formatters import format_inr_cr, score_color

GEOJSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "seed", "india_boundary.geojson")


def render(master_df):
    st.title("Location Heat Map")

    if master_df.empty:
        st.warning("No location data available.")
        return

    # --- Filters ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        states = st.multiselect("State", sorted(master_df["state"].unique()), default=[])
    with c2:
        tiers = st.multiselect("Tier", sorted(master_df["tier"].unique()), default=[])
    with c3:
        score_range = st.slider("Score Range", 0, 100, (0, 100))
    with c4:
        formats = st.multiselect("Format", sorted(master_df["format_name"].unique()), default=[])

    df = master_df.copy()
    if states:
        df = df[df["state"].isin(states)]
    if tiers:
        df = df[df["tier"].isin(tiers)]
    df = df[(df["composite_score"] >= score_range[0]) & (df["composite_score"] <= score_range[1])]
    if formats:
        df = df[df["format_name"].isin(formats)]

    viable_npv = df[df["viable"]]["npv_cr"].sum() if "viable" in df.columns else 0
    st.caption(f"Showing **{len(df)}** of {len(master_df)} locations | "
               f"Avg Score: **{df['composite_score'].mean():.0f}** | "
               f"Total NPV: **{format_inr_cr(viable_npv)}**")

    # --- Map with official India boundary ---
    # Use no-labels tile to avoid showing disputed international boundaries
    m = folium.Map(
        location=[23.5, 79],
        zoom_start=5,
        tiles=None,
        width="100%",
        height="100%",
    )

    # Add a clean base tile WITHOUT political boundary labels
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://carto.com/">CARTO</a>',
        name="Base Map",
        control=False,
    ).add_to(m)

    # Add official India boundary (Government of India — includes full J&K, Ladakh, PoK, Aksai Chin)
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, "r") as f:
            india_geojson = json.load(f)
        folium.GeoJson(
            india_geojson,
            name="India Boundary",
            style_function=lambda x: {
                "fillColor": "#E8F5E9",
                "color": "#1B5E3B",
                "weight": 2.5,
                "fillOpacity": 0.15,
                "dashArray": "",
            },
        ).add_to(m)

    # Heat layer
    heat_data = [[row["lat"], row["lng"], row["composite_score"] / 100] for _, row in df.iterrows()]
    if heat_data:
        HeatMap(
            heat_data, radius=30, blur=20, max_zoom=10,
            gradient={0.2: "#DC2626", 0.5: "#F59E0B", 0.8: "#22C55E", 1.0: "#16A34A"},
        ).add_to(m)

    # Markers
    for _, row in df.iterrows():
        score = row["composite_score"]
        color = score_color(score)
        radius = max(5, min(18, score / 6))

        popup_html = (
            f'<div style="font-family:Inter,sans-serif;width:240px">'
            f'<b style="font-size:14px">{row["name"]}</b><br>'
            f'<span style="color:#666;font-size:11px">{row["state"]} &middot; {row["tier"].upper()}</span>'
            f'<hr style="margin:6px 0;border-color:#eee">'
            f'<b>Score:</b> <span style="color:{color};font-weight:700">{score}/100</span><br>'
            f'<b>Format:</b> {row["format_icon"]} {row["format_name"]}<br>'
            f'<b>15Y NPV:</b> {format_inr_cr(row["npv_cr"])}<br>'
            f'<b>Payback:</b> {row["payback_years"]:.1f} years<br>'
            f'<b>Action:</b> {row["action"]}'
            f'</div>'
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{row['name']} — Score: {score}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=None, height=620, returned_objects=[])

    # --- Table below map ---
    with st.expander(f"View Location Data ({len(df)} locations)"):
        display_cols = ["name", "state", "tier", "composite_score", "format_icon", "format_name",
                        "npv_cr", "payback_years", "irr_pct", "action"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols].reset_index(drop=True), use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False)
        st.download_button("Download Filtered Data", csv, "filtered_locations.csv", "text/csv")
