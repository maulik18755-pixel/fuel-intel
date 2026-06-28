"""Location Deep Dive — single-location analysis with financials and sensitivity."""
import streamlit as st
import plotly.graph_objects as go
from ui.theme import kpi_card, insight_box
from utils.formatters import format_inr_cr, score_color
from core.scoring_engine import ScoringEngine, PILLAR_NAMES
from core.format_recommender import FormatRecommender
from core.profitability_model import ProfitabilityModel


def render(master_df, profitability_model, format_recommender):
    st.title("Location Deep Dive")

    if master_df.empty:
        st.warning("No data loaded.")
        return

    options = master_df.apply(lambda r: f"{r['name']} — Score: {r['composite_score']}", axis=1).tolist()
    selected = st.selectbox("Select a location for detailed analysis", options)
    idx = options.index(selected)
    loc = master_df.iloc[idx]
    loc_dict = loc.to_dict()

    # --- Header ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.header(loc["name"])
        st.caption(f'{loc["state"]} · {loc["tier"].upper()}')
        strengths = loc.get("key_strengths", [])
        gaps = loc.get("key_gaps", [])
        if isinstance(strengths, list) and isinstance(gaps, list) and len(strengths) >= 1 and len(gaps) >= 1:
            st.markdown(f"Strong **{PILLAR_NAMES.get(strengths[0], strengths[0])}** and "
                       f"**{PILLAR_NAMES.get(strengths[1], '') if len(strengths) > 1 else ''}** fundamentals "
                       f"with room to improve **{PILLAR_NAMES.get(gaps[0], gaps[0])}**.")
    with c2:
        color = score_color(loc["composite_score"])
        st.markdown(f"""<div style="text-align:center;padding:16px;background:white;border:2px solid {color};border-radius:14px">
            <div style="font-size:2.6rem;font-weight:800;color:{color}">{loc['composite_score']}</div>
            <div style="font-size:0.8rem;color:#666;margin-top:2px">LOCATION SCORE</div>
            <div style="font-size:0.78rem;font-weight:600;color:{color};margin-top:4px">{loc['score_tier']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Pillar Breakdown ---
    st.subheader("Scoring Breakdown")
    pillar_keys = ["demand", "competition", "income", "ev_readiness", "infrastructure", "growth_trajectory"]
    pillar_values = []
    for k in pillar_keys:
        v = float(loc.get(k, 50))
        pillar_values.append(100 - v if k == "competition" else v)

    labels = [PILLAR_NAMES.get(k, k) for k in pillar_keys]

    c1, c2 = st.columns([1, 1])
    with c1:
        fig = go.Figure(data=go.Scatterpolar(
            r=pillar_values + [pillar_values[0]],
            theta=labels + [labels[0]],
            fill="toself", fillcolor="rgba(0,51,153,0.12)",
            line=dict(color="#003399", width=2),
            marker=dict(size=6, color="#003399"),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9)),
                       angularaxis=dict(tickfont=dict(size=11, family="Inter"))),
            showlegend=False, margin=dict(t=30, b=30, l=60, r=60), height=340,
            paper_bgcolor="#FAFBFE",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        for k, v, label in zip(pillar_keys, pillar_values, labels):
            icon = "🟢" if v >= 70 else "🟡" if v >= 45 else "🔴"
            st.markdown(f"**{icon} {label}:** {v:.0f}/100")
        st.caption("Competition score is inverted — lower competition yields a higher opportunity score.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Format Recommendation ---
    st.subheader("Recommended Station Format")
    fmt = format_recommender.recommend(loc_dict)
    fc1, fc2 = st.columns([1, 1])
    with fc1:
        st.markdown(f"### {fmt['icon']} {fmt['name']}")
        st.markdown(fmt["description"])
        st.markdown(f"**Fuel Points:** {fmt['fuel_dispensing_points'][0]}-{fmt['fuel_dispensing_points'][1]} · "
                    f"**EV Chargers:** {fmt['ev_chargers'][0]}-{fmt['ev_chargers'][1]} ({fmt['charger_type']})")
        st.markdown(f"**Retail Space:** {fmt['retail_sqft'][0]}-{fmt['retail_sqft'][1]} sqft · "
                    f"**Footprint:** {fmt['footprint_sqft'][0]:,}-{fmt['footprint_sqft'][1]:,} sqft")
        st.markdown(f"**CAPEX:** {format_inr_cr(fmt['capex_cr'])}")
    with fc2:
        st.markdown("**Amenities:**")
        for a in fmt.get("amenities", []):
            st.markdown(f"  • {a}")
        st.markdown("**10-Year Transition Plan:**")
        tp = fmt.get("transition_plan", {})
        for year, action in tp.items():
            st.markdown(f"  **{year.replace('_', ' ').title()}:** {action}")
    st.caption(f"**Reasoning:** {fmt.get('reasoning', '')}")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # --- Financial Projection ---
    st.subheader("15-Year Financial Projection")
    profit = profitability_model.project_cash_flows(loc_dict, fmt)
    flows = profit["annual_cash_flows"]

    kc = st.columns(5)
    with kc[0]:
        st.markdown(kpi_card(format_inr_cr(profit["total_investment_cr"]), "Total Investment"), unsafe_allow_html=True)
    with kc[1]:
        st.markdown(kpi_card(format_inr_cr(profit["npv_cr"]), "15-Year Net Value"), unsafe_allow_html=True)
    with kc[2]:
        st.markdown(kpi_card(f"{profit['irr_pct']:.1f}%", "IRR"), unsafe_allow_html=True)
    with kc[3]:
        pb = f"{profit['payback_years']:.1f}Y" if profit["viable"] else "Not viable"
        st.markdown(kpi_card(pb, "Payback Period"), unsafe_allow_html=True)
    with kc[4]:
        st.markdown(kpi_card(format_inr_cr(profit["peak_annual_revenue_cr"]), "Peak Revenue/Year"), unsafe_allow_html=True)

    # Revenue stacked area
    years = [f["year"] for f in flows]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=years, y=[f["fuel_revenue_cr"] for f in flows],
                              name="Fuel", stackgroup="one", line=dict(width=0), fillcolor="rgba(0,51,153,0.6)"))
    fig2.add_trace(go.Scatter(x=years, y=[f["ev_revenue_cr"] for f in flows],
                              name="EV Charging", stackgroup="one", line=dict(width=0), fillcolor="rgba(5,150,105,0.6)"))
    fig2.add_trace(go.Scatter(x=years, y=[f["retail_revenue_cr"] for f in flows],
                              name="Retail", stackgroup="one", line=dict(width=0), fillcolor="rgba(255,102,0,0.5)"))
    fig2.add_trace(go.Scatter(x=years, y=[f["cumulative_cf_cr"] for f in flows],
                              name="Cumulative CF", line=dict(color="#DC2626", width=2, dash="dot"),
                              yaxis="y2"))
    fig2.update_layout(
        title="Revenue Breakdown & Cumulative Cash Flow",
        xaxis_title="Year", yaxis_title="Annual Revenue (₹ Cr)",
        yaxis2=dict(title="Cumulative CF (₹ Cr)", overlaying="y", side="right"),
        height=400, margin=dict(t=40, b=40),
        paper_bgcolor="#FAFBFE", plot_bgcolor="#FAFBFE",
        font=dict(family="Inter"), legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # --- Sensitivity ---
    st.subheader("Score Sensitivity Analysis")
    engine = ScoringEngine()
    sensitivities = engine.full_sensitivity(loc_dict, delta_pct=20.0)

    fig3 = go.Figure()
    for s in sensitivities:
        fig3.add_trace(go.Bar(
            y=[s["pillar_name"]], x=[s["score_if_high"] - s["base_score"]],
            name=f'+20%', orientation='h', marker_color="#059669", showlegend=False,
            text=[f"+{s['score_if_high'] - s['base_score']}"], textposition="outside",
        ))
        fig3.add_trace(go.Bar(
            y=[s["pillar_name"]], x=[s["score_if_low"] - s["base_score"]],
            name=f'-20%', orientation='h', marker_color="#DC2626", showlegend=False,
            text=[f"{s['score_if_low'] - s['base_score']}"], textposition="outside",
        ))
    fig3.update_layout(
        title="Impact of ±20% Change in Each Pillar on Composite Score",
        xaxis_title="Score Change", barmode="relative", height=300,
        margin=dict(t=40, b=30), paper_bgcolor="#FAFBFE", plot_bgcolor="#FAFBFE",
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📋 Detailed Cash Flow Table"):
        import pandas as pd
        cf_df = pd.DataFrame(flows)
        st.dataframe(cf_df, use_container_width=True, hide_index=True)
