"""Investment Priority Matrix — 2×2 quadrant chart for capital allocation."""
import streamlit as st
import plotly.graph_objects as go
from utils.formatters import format_inr_cr


FORMAT_COLORS = {
    "large_highway_hub": "#003399", "urban_full_service": "#0052CC",
    "ev_focused_station": "#059669", "compact_urban": "#D97706", "hybrid_transition": "#FF6600",
}


def render(master_df):
    st.title("Investment Priority Matrix")
    st.caption("Portfolio prioritization for capital allocation decisions")

    if master_df.empty:
        st.warning("No data.")
        return

    df = master_df[master_df["viable"] == True].copy()

    x_col = "composite_score"
    y_col = "npv_cr"
    x_label = "Market Attractiveness (Score)"
    y_label = "Financial Return (15Y NPV ₹Cr)"

    x_mid = df[x_col].median()
    y_mid = max(df[y_col].median(), 0)

    # Quadrant assignment
    def assign_quadrant(row):
        if row[x_col] >= x_mid and row[y_col] >= y_mid:
            return "FAST TRACK"
        elif row[x_col] < x_mid and row[y_col] >= y_mid:
            return "SELECTIVE INVEST"
        elif row[x_col] >= x_mid and row[y_col] < y_mid:
            return "STRATEGIC HOLD"
        return "DEPRIORITIZE"

    df["quadrant"] = df.apply(assign_quadrant, axis=1)

    quad_colors = {"FAST TRACK": "#059669", "SELECTIVE INVEST": "#D97706",
                   "STRATEGIC HOLD": "#003399", "DEPRIORITIZE": "#9CA3AF"}

    fig = go.Figure()

    # Background quadrant shapes
    x_range = [df[x_col].min() - 5, df[x_col].max() + 5]
    y_range = [df[y_col].min() - 2, df[y_col].max() + 2]
    fig.add_shape(type="rect", x0=x_mid, x1=x_range[1], y0=y_mid, y1=y_range[1],
                  fillcolor="rgba(5,150,105,0.06)", line=dict(width=0))
    fig.add_shape(type="rect", x0=x_range[0], x1=x_mid, y0=y_mid, y1=y_range[1],
                  fillcolor="rgba(217,119,6,0.06)", line=dict(width=0))
    fig.add_shape(type="rect", x0=x_mid, x1=x_range[1], y0=y_range[0], y1=y_mid,
                  fillcolor="rgba(0,51,153,0.06)", line=dict(width=0))
    fig.add_shape(type="rect", x0=x_range[0], x1=x_mid, y0=y_range[0], y1=y_mid,
                  fillcolor="rgba(156,163,175,0.06)", line=dict(width=0))

    # Quadrant labels
    fig.add_annotation(x=x_range[1]-2, y=y_range[1]-0.5, text="FAST TRACK", font=dict(size=12, color="#059669", family="Inter"), showarrow=False)
    fig.add_annotation(x=x_range[0]+5, y=y_range[1]-0.5, text="SELECTIVE INVEST", font=dict(size=12, color="#D97706", family="Inter"), showarrow=False)
    fig.add_annotation(x=x_range[1]-2, y=y_range[0]+0.5, text="STRATEGIC HOLD", font=dict(size=12, color="#003399", family="Inter"), showarrow=False)
    fig.add_annotation(x=x_range[0]+5, y=y_range[0]+0.5, text="DEPRIORITIZE", font=dict(size=12, color="#9CA3AF", family="Inter"), showarrow=False)

    for _, row in df.iterrows():
        color = FORMAT_COLORS.get(row["format_code"], "#999")
        fig.add_trace(go.Scatter(
            x=[row[x_col]], y=[row[y_col]],
            mode="markers+text",
            text=[row["name"].split(" - ")[0][:15]],
            textposition="top center", textfont=dict(size=8, family="Inter"),
            marker=dict(size=max(8, row.get("npv_cr", 5) * 1.2), color=color, opacity=0.8,
                        line=dict(width=1, color="white")),
            hovertext=f"{row['name']}<br>Score: {row['composite_score']}<br>NPV: {format_inr_cr(row['npv_cr'])}<br>Format: {row['format_name']}<br>Quadrant: {row['quadrant']}",
            hoverinfo="text", showlegend=False,
        ))

    # Median lines
    fig.add_hline(y=y_mid, line_dash="dot", line_color="#aaa", line_width=1)
    fig.add_vline(x=x_mid, line_dash="dot", line_color="#aaa", line_width=1)

    fig.update_layout(
        xaxis_title=x_label, yaxis_title=y_label,
        height=520, margin=dict(t=20, b=50, l=50, r=20),
        paper_bgcolor="#FAFBFE", plot_bgcolor="#FAFBFE",
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Quadrant summaries
    st.subheader("Quadrant Summary")
    for q_name, q_color in quad_colors.items():
        q_df = df[df["quadrant"] == q_name]
        if len(q_df) == 0:
            continue
        total_npv = q_df["npv_cr"].sum()
        locs = ", ".join(q_df["name"].head(5).tolist())
        actions = {
            "FAST TRACK": "Acquire land, begin construction within 6 months.",
            "SELECTIVE INVEST": "Viable if specific market conditions improve. Conduct detailed feasibility.",
            "STRATEGIC HOLD": "Attractive market but returns need optimization. Consider smaller format or phased investment.",
            "DEPRIORITIZE": "Revisit in 2-3 years or if market conditions change significantly.",
        }
        with st.expander(f"**{q_name}** — {len(q_df)} locations | Total NPV: {format_inr_cr(total_npv)}"):
            st.markdown(f"**Action:** {actions.get(q_name, '')}")
            st.markdown(f"**Locations:** {locs}")
            st.dataframe(q_df[["name", "state", "composite_score", "format_name", "npv_cr", "payback_years"]].reset_index(drop=True),
                        use_container_width=True, hide_index=True)
