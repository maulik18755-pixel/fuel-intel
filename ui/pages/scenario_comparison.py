"""Scenario Comparison — compare different strategic weight configurations."""
import streamlit as st
import plotly.graph_objects as go
from core.scoring_engine import ScoringEngine, load_locations_from_csv
import os


SCENARIOS = {
    "Base Case": {"demand": 0.30, "competition": 0.20, "income": 0.15, "ev_readiness": 0.15, "infrastructure": 0.10, "growth_trajectory": 0.10},
    "EV-First Strategy": {"demand": 0.25, "competition": 0.15, "income": 0.15, "ev_readiness": 0.30, "infrastructure": 0.10, "growth_trajectory": 0.05},
    "Fuel Maximizer": {"demand": 0.40, "competition": 0.25, "income": 0.15, "ev_readiness": 0.05, "infrastructure": 0.10, "growth_trajectory": 0.05},
    "Growth Corridor": {"demand": 0.20, "competition": 0.15, "income": 0.10, "ev_readiness": 0.10, "infrastructure": 0.15, "growth_trajectory": 0.30},
}


def render(master_df, scoring_engine):
    st.title("Scenario Comparison")
    st.caption("See how different strategic priorities change the investment picture")

    scenario_name = st.radio("Select scenario to compare against Base Case", list(SCENARIOS.keys())[1:], horizontal=True)

    base_weights = SCENARIOS["Base Case"]
    alt_weights = SCENARIOS[scenario_name]

    locations = master_df.to_dict("records")

    base_engine = ScoringEngine(base_weights)
    alt_engine = ScoringEngine(alt_weights)

    rows = []
    for loc in locations:
        base_scored = base_engine.score_location(loc)
        alt_scored = alt_engine.score_location(loc)
        rows.append({
            "name": loc.get("name", ""),
            "state": loc.get("state", ""),
            "base_score": base_scored["composite_score"],
            "alt_score": alt_scored["composite_score"],
        })

    import pandas as pd
    comp_df = pd.DataFrame(rows).sort_values("base_score", ascending=False).reset_index(drop=True)
    comp_df["rank_base"] = range(1, len(comp_df) + 1)
    comp_df = comp_df.sort_values("alt_score", ascending=False).reset_index(drop=True)
    comp_df["rank_alt"] = range(1, len(comp_df) + 1)
    comp_df["rank_change"] = comp_df["rank_base"] - comp_df["rank_alt"]
    comp_df["score_delta"] = comp_df["alt_score"] - comp_df["base_score"]
    comp_df = comp_df.sort_values("base_score", ascending=False).reset_index(drop=True)

    # Scatter plot
    st.subheader(f"Base Case vs {scenario_name}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=comp_df["base_score"], y=comp_df["alt_score"],
        mode="markers+text", text=comp_df["name"].str.split(" - ").str[0],
        textposition="top center", textfont=dict(size=8),
        marker=dict(size=10, color=comp_df["score_delta"], colorscale="RdYlGn", cmin=-15, cmax=15,
                    showscale=True, colorbar=dict(title="Δ Score")),
    ))
    fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines",
                             line=dict(color="#ccc", dash="dash"), showlegend=False))
    fig.update_layout(
        xaxis_title="Base Case Score", yaxis_title=f"{scenario_name} Score",
        height=480, margin=dict(t=20, b=40),
        paper_bgcolor="#FAFBFE", plot_bgcolor="#FAFBFE",
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Points above the diagonal benefit from this scenario; points below are disadvantaged.")

    # Top movers
    st.subheader("Biggest Rank Changes")
    movers = comp_df.sort_values("rank_change", ascending=False)
    display = movers[["name", "state", "base_score", "alt_score", "rank_base", "rank_alt", "rank_change"]].head(10)
    display.columns = ["Location", "State", "Base Score", f"{scenario_name} Score", "Base Rank", "New Rank", "Rank Δ"]
    st.dataframe(display, use_container_width=True, hide_index=True)

    # Weight comparison
    st.subheader("Weight Configuration")
    wc1, wc2 = st.columns(2)
    with wc1:
        st.markdown("**Base Case**")
        for k, v in base_weights.items():
            st.progress(v, text=f"{k.replace('_', ' ').title()}: {v:.0%}")
    with wc2:
        st.markdown(f"**{scenario_name}**")
        for k, v in alt_weights.items():
            st.progress(v, text=f"{k.replace('_', ' ').title()}: {v:.0%}")
