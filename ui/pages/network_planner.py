"""Network Planner — select optimal fuel retail network with constraints."""
import streamlit as st
import plotly.graph_objects as go
from core.network_optimizer import NetworkOptimizer
from ui.theme import kpi_card, insight_box, rec_card
from utils.formatters import format_inr_cr


def render(master_df):
    st.title("Network Planner")
    st.caption("Select the optimal network of stations given budget, spacing, and coverage constraints")

    if master_df.empty:
        st.warning("No candidate data available.")
        return

    # --- Controls ---
    st.subheader("Network Parameters")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        target = st.number_input("Target Stations", 10, 500, 100, step=10)
    with c2:
        budget = st.number_input("Budget (₹ Cr)", 100, 50000, 2000, step=100)
    with c3:
        spacing = st.number_input("Min Spacing (km)", 5, 50, 15, step=5)
    with c4:
        highway_spacing = st.number_input("Highway Spacing (km)", 10, 80, 30, step=5)

    diversity = st.slider("Max % from any single state", 10, 50, 25, step=5) / 100

    # --- Run optimizer ---
    optimizer = NetworkOptimizer()
    result = optimizer.optimize(
        master_df,
        target_count=target,
        budget_cr=budget,
        min_spacing_km=spacing,
        min_spacing_highway_km=highway_spacing,
        state_max_pct=diversity,
    )

    selected = result["selected"]
    summary = result["summary"]
    log = result["constraint_log"]

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Results ---
    st.markdown(insight_box(
        "Network Selection Complete",
        f"Selected <b>{summary['total_selected']}</b> stations from {summary['total_candidates']} candidates "
        f"across <b>{summary['states_covered']} states</b>. "
        f"Total CAPEX: <b>{format_inr_cr(summary['total_capex_cr'])}</b>. "
        f"Portfolio NPV: <b>{format_inr_cr(summary['total_npv_cr'])}</b>. "
        f"Average score: <b>{summary['avg_score']}</b>. "
        f"Rejected {summary['spacing_rejections']} for spacing, "
        f"{summary['budget_rejections']} for budget, "
        f"{summary['diversity_rejections']} for state diversity."
    ), unsafe_allow_html=True)

    # KPI cards
    kc = st.columns(5)
    with kc[0]:
        st.markdown(kpi_card(str(summary["total_selected"]), "Stations Selected", f"of {summary['total_candidates']} candidates"), unsafe_allow_html=True)
    with kc[1]:
        st.markdown(kpi_card(format_inr_cr(summary["total_capex_cr"]), "Total CAPEX", f"of {format_inr_cr(budget)} budget"), unsafe_allow_html=True)
    with kc[2]:
        st.markdown(kpi_card(format_inr_cr(summary["total_npv_cr"]), "Portfolio NPV (15Y)"), unsafe_allow_html=True)
    with kc[3]:
        st.markdown(kpi_card(str(summary["states_covered"]), "States Covered"), unsafe_allow_html=True)
    with kc[4]:
        st.markdown(kpi_card(str(summary["avg_score"]), "Avg Score"), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Tier and Format breakdown ---
    st.subheader("Network Composition")
    c1, c2 = st.columns(2)

    with c1:
        tier_mix = summary.get("tier_mix", {})
        if tier_mix:
            fig1 = go.Figure(data=[go.Pie(
                labels=list(tier_mix.keys()), values=list(tier_mix.values()),
                hole=0.5, textinfo="label+value+percent", textposition="outside",
                marker_colors=["#1B5E3B", "#1B7A42", "#22C55E", "#4CAF50", "#81C784"],
                textfont=dict(size=11, family="Inter"),
            )])
            fig1.update_layout(title="By Location Tier", showlegend=False,
                               margin=dict(t=40, b=10), height=300,
                               paper_bgcolor="#FAFDF9", font=dict(family="Inter"))
            st.plotly_chart(fig1, use_container_width=True)

    with c2:
        fmt_mix = summary.get("format_mix", {})
        if fmt_mix:
            fig2 = go.Figure(data=[go.Pie(
                labels=list(fmt_mix.keys()), values=list(fmt_mix.values()),
                hole=0.5, textinfo="label+value+percent", textposition="outside",
                marker_colors=["#1B5E3B", "#1B7A42", "#22C55E", "#F59E0B", "#4CAF50"],
                textfont=dict(size=11, family="Inter"),
            )])
            fig2.update_layout(title="By Station Format", showlegend=False,
                               margin=dict(t=40, b=10), height=300,
                               paper_bgcolor="#FAFDF9", font=dict(family="Inter"))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- State distribution ---
    st.subheader("Geographic Distribution")
    if not selected.empty:
        state_dist = selected["state"].value_counts().sort_values(ascending=True).tail(15)
        fig3 = go.Figure(data=[go.Bar(
            y=state_dist.index, x=state_dist.values, orientation="h",
            marker_color="#22C55E", text=state_dist.values, textposition="outside",
            textfont=dict(size=12, family="Inter"),
        )])
        fig3.update_layout(
            xaxis_title="Stations Selected", height=400,
            margin=dict(l=10, r=40, t=10, b=40),
            paper_bgcolor="#FAFDF9", plot_bgcolor="#FAFDF9",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Phasing ---
    st.subheader("Deployment Phasing")
    phases = optimizer.phase_network(selected)
    for phase_key, phase_data in phases.items():
        p_locs = phase_data["locations"]
        if p_locs.empty:
            continue
        st.markdown(rec_card(
            f"{phase_data['name']} — {len(p_locs)} stations",
            f"Top locations: {', '.join(p_locs['name'].head(5).tolist())}. "
            f"Avg score: {p_locs['composite_score'].mean():.0f}."
        ), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Selected locations table ---
    st.subheader("Selected Network")
    if not selected.empty:
        display_cols = ["network_rank", "name", "state", "tier", "composite_score",
                        "format_icon", "format_name", "npv_cr", "payback_years", "source"]
        available = [c for c in display_cols if c in selected.columns]
        st.dataframe(selected[available], use_container_width=True, hide_index=True,
                     height=400)

    # --- Constraint log ---
    with st.expander(f"Constraint Log ({len(log)} rejections)"):
        if log:
            import pandas as pd
            log_df = pd.DataFrame(log)
            st.dataframe(log_df, use_container_width=True, hide_index=True, height=300)
        else:
            st.info("No candidates were rejected.")

    # --- Export ---
    if not selected.empty:
        csv = selected.to_csv(index=False)
        st.download_button("Download Selected Network (CSV)", csv, "selected_network.csv", "text/csv")
