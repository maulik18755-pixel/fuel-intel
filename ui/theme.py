"""
Clean energy theme — light green, high readability, professional.
All HTML helpers use single-line format to prevent Streamlit markdown rendering bugs.
"""

BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

h1 { font-weight: 800; color: #1B5E3B; font-size: 1.9rem; letter-spacing: -0.02em; }
h2 { font-weight: 700; color: #1E293B; font-size: 1.35rem; }
h3 { font-weight: 600; color: #1E293B; font-size: 1.05rem; }

.kpi-card {
    background: white; border: 1px solid #D5E8D4; border-radius: 12px;
    padding: 22px 18px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}
.kpi-value { font-size: 2rem; font-weight: 800; color: #1B7A42; line-height: 1.1; }
.kpi-label { font-size: 0.78rem; color: #64748B; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
.kpi-delta { font-size: 0.78rem; margin-top: 6px; font-weight: 600; }
.kpi-delta.pos { color: #22C55E; }
.kpi-delta.neg { color: #DC2626; }

.insight-box {
    background: linear-gradient(135deg, #1B5E3B 0%, #22804A 50%, #2E9B5C 100%);
    color: white; border-radius: 14px; padding: 24px 28px; margin: 12px 0;
    box-shadow: 0 4px 12px rgba(27,94,59,0.2);
}
.insight-box .ib-title { font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #C6F6D5; margin-bottom: 10px; }
.insight-box .ib-body { font-size: 0.95rem; line-height: 1.7; color: #F0FFF4; }

.rec-card {
    background: white; border-left: 4px solid #22C55E; border-radius: 0 10px 10px 0;
    padding: 16px 20px; margin: 8px 0; box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}
.rec-card .rc-title { font-weight: 700; color: #1B5E3B; font-size: 0.95rem; margin-bottom: 6px; }
.rec-card .rc-body { font-size: 0.88rem; color: #475569; line-height: 1.6; }

.score-badge { display: inline-block; padding: 4px 12px; border-radius: 16px; font-weight: 700; font-size: 0.82rem; }
.sb-high { background: #DCFCE7; color: #14532D; }
.sb-mid { background: #FEF9C3; color: #854D0E; }
.sb-low { background: #FEE2E2; color: #991B1B; }

.section-divider { border: none; border-top: 2px solid #22C55E; margin: 28px 0 18px 0; opacity: 0.18; }

/* Sidebar — light sage green with dark text for readability */
section[data-testid="stSidebar"] { background: #E8F5E9 !important; }
section[data-testid="stSidebar"] * { color: #1B5E3B !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover { background: rgba(27,94,59,0.08); border-radius: 6px; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] { background: rgba(27,94,59,0.12); border-radius: 6px; }
</style>
"""


def kpi_card(value: str, label: str, delta: str = None, delta_pos: bool = True) -> str:
    if delta:
        cls = "pos" if delta_pos else "neg"
        delta_part = f'<div class="kpi-delta {cls}">{delta}</div>'
    else:
        delta_part = ""
    return f'<div class="kpi-card"><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div>{delta_part}</div>'


def insight_box(title: str, body: str) -> str:
    return f'<div class="insight-box"><div class="ib-title">{title}</div><div class="ib-body">{body}</div></div>'


def rec_card(title: str, body: str) -> str:
    return f'<div class="rec-card"><div class="rc-title">{title}</div><div class="rc-body">{body}</div></div>'


def score_badge(score: int) -> str:
    if score >= 70:
        cls = "sb-high"
    elif score >= 45:
        cls = "sb-mid"
    else:
        cls = "sb-low"
    return f'<span class="score-badge {cls}">{score}</span>'
