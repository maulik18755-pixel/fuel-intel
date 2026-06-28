"""Executive Summary — CEO-level overview with headline insights and recommendations."""
import streamlit as st
import plotly.graph_objects as go
from ui.theme import kpi_card, insight_box, rec_card
from utils.formatters import format_inr_cr, score_color


def render(master_df, registry):
    st.title("Executive Summary")
    st.caption("Strategic analysis of fuel retail & EV charging expansion opportunities across India")

    if master_df.empty:
        st.warning("No data loaded. Check data sources.")
        return

    # --- Compute stats ---
    n = len(master_df)
    n_high = len(master_df[master_df["composite_score"] >= 70])
    n_states = master_df["state"].nunique()
    total_npv = master_df[master_df["viable"] == True]["npv_cr"].sum()
    avg_payback = master_df[master_df["viable"] == True]["payback_years"].mean()
    n_ev = len(master_df[master_df["format_code"].isin(["ev_focused_station", "hybrid_transition"])])
    top_state = master_df[master_df["composite_score"] >= 70]["state"].value_counts().index[0] if n_high > 0 else "N/A"

    # --- 1. Headline Insight ---
    st.markdown(insight_box(
        "Key Finding",
        f"Analysis of <b>{n}</b> candidate locations across <b>{n_states} states</b> identifies "
        f"<b>{n_high} high-potential sites</b> with combined 15-year net value of <b>{format_inr_cr(total_npv)}</b>. "
        f"<b>{top_state}</b> shows the strongest cluster of opportunities. "
        f"<b>{n_ev}</b> locations warrant EV-focused or hybrid transition formats based on current adoption trajectory."
    ), unsafe_allow_html=True)

    # --- 2. KPI Cards ---
    cols = st.columns(4)
    with cols[0]:
        st.markdown(kpi_card(str(n), "Locations Analyzed"), unsafe_allow_html=True)
    with cols[1]:
        pct = f"{n_high / n * 100:.0f}% of total" if n > 0 else ""
        st.markdown(kpi_card(str(n_high), "High Potential Sites", pct, True), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(kpi_card(format_inr_cr(total_npv), "Portfolio Net Value (15Y)"), unsafe_allow_html=True)
    with cols[3]:
        pb = f"{avg_payback:.1f} yrs" if avg_payback == avg_payback else "—"
        st.markdown(kpi_card(pb, "Avg Payback Period"), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 3. Top 10 Locations Table ---
    st.subheader("Top Investment Targets")
    top10 = master_df.head(10)[["name", "state", "composite_score", "format_icon", "format_name",
                                 "npv_cr", "payback_years", "irr_pct", "action"]].copy()
    top10.columns = ["Location", "State", "Score", "Fmt", "Format", "NPV (₹Cr)", "Payback (Y)", "IRR %", "Action"]
    top10.insert(0, "Rank", range(1, len(top10) + 1))
    st.dataframe(top10, use_container_width=True, hide_index=True,
                 column_config={
                     "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
                     "NPV (₹Cr)": st.column_config.NumberColumn(format="%.1f"),
                     "Payback (Y)": st.column_config.NumberColumn(format="%.1f"),
                     "IRR %": st.column_config.NumberColumn(format="%.1f"),
                 })

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 4. Format Mix ---
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Recommended Format Mix")
        fmt_counts = master_df["format_name"].value_counts()
        colors = {"Large Highway Hub": "#1B5E3B", "Urban Full-Service": "#1B7A42",
                  "EV-Focused Station": "#22C55E", "Compact Urban": "#F59E0B",
                  "Hybrid Transition": "#4CAF50"}
        fig = go.Figure(data=[go.Pie(
            labels=fmt_counts.index, values=fmt_counts.values,
            hole=0.55, marker_colors=[colors.get(l, "#999") for l in fmt_counts.index],
            textinfo="label+percent", textposition="outside",
            textfont=dict(size=11, family="Inter"),
        )])
        fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
                          paper_bgcolor="#FAFDF9", plot_bgcolor="#FAFDF9", height=320,
                          font=dict(family="Inter"))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Strategic Implication")
        dominant = fmt_counts.index[0] if len(fmt_counts) > 0 else "N/A"
        dom_pct = fmt_counts.iloc[0] / n * 100 if n > 0 else 0
        n_hybrid = len(master_df[master_df["format_code"] == "hybrid_transition"])
        st.markdown(f"""
        The portfolio composition shows **{dominant}** as the dominant recommendation
        ({dom_pct:.0f}% of locations), reflecting India's current energy transition stage.

        **{n_hybrid}** locations are recommended for Hybrid Transition format — these are
        pre-wired for EV conversion and should be upgraded as state-level EV penetration
        crosses 15% (projected 2028-30 for leading states).

        EV-Focused stations are concentrated in **metro and emerging** corridors where
        charging infrastructure and high-income demographics already support adoption.
        """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 5. State Opportunity Map ---
    st.subheader("State-wise Opportunity Concentration")
    state_scores = master_df[master_df["composite_score"] >= 45].groupby("state").agg(
        count=("composite_score", "size"),
        avg_score=("composite_score", "mean"),
        total_npv=("npv_cr", "sum"),
    ).sort_values("count", ascending=True).tail(12)

    fig2 = go.Figure(data=[go.Bar(
        y=state_scores.index, x=state_scores["count"], orientation="h",
        marker_color="#22C55E", text=state_scores["count"], textposition="outside",
        textfont=dict(size=12, family="Inter"),
    )])
    fig2.update_layout(
        xaxis_title="Number of Viable Locations",
        yaxis_title="", height=380, margin=dict(l=10, r=40, t=10, b=40),
        paper_bgcolor="#FAFDF9", plot_bgcolor="#FAFDF9",
        font=dict(family="Inter", size=12),
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- 6. Investment Phasing ---
    st.subheader("Investment Phasing Recommendation")
    fast_track = master_df[master_df["action"].str.contains("Fast-Track")]
    feasibility = master_df[master_df["action"].str.contains("Feasibility")]
    monitor = master_df[master_df["action"].str.contains("Monitor")]

    ft_names = ", ".join(fast_track["name"].head(5).tolist()) if len(fast_track) > 0 else "None identified"
    ft_capex = fast_track["npv_cr"].sum() if len(fast_track) > 0 else 0

    st.markdown(rec_card(
        f"Phase 1: Immediate (0-12 months) — {len(fast_track)} locations",
        f"{ft_names}. Combined portfolio value: {format_inr_cr(ft_capex)}. "
        f"These sites have scores ≥80 and payback ≤5 years. Recommend initiating land acquisition and regulatory approvals."
    ), unsafe_allow_html=True)

    fs_names = ", ".join(feasibility["name"].head(5).tolist()) if len(feasibility) > 0 else "None"
    st.markdown(rec_card(
        f"Phase 2: Near-Term (12-24 months) — {len(feasibility)} locations",
        f"{fs_names}. These require detailed feasibility studies on land availability, grid capacity, and competitive landscape before commitment."
    ), unsafe_allow_html=True)

    st.markdown(rec_card(
        f"Phase 3: Strategic Pipeline (24-36 months) — {len(monitor)} locations",
        f"{len(monitor)} locations under monitoring. Trigger conditions: score improvement from new highway completion, "
        f"EV adoption crossing 10% in the state, or competitor exit creating market gap."
    ), unsafe_allow_html=True)

    # --- 7. Export ---
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    csv = master_df.to_csv(index=False)
    st.download_button("📥 Download Full Analysis Report (CSV)", csv, "fuel_intel_full_report.csv", "text/csv")
