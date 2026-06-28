"""
Reliance brand theme — CSS, KPI cards, insight boxes, and styled components.
"""

BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

h1 { font-weight: 800; color: #003399; font-size: 1.9rem; letter-spacing: -0.02em; }
h2 { font-weight: 700; color: #1A1A2E; font-size: 1.35rem; }
h3 { font-weight: 600; color: #1A1A2E; font-size: 1.05rem; }

.kpi-card {
    background: white; border: 1px solid #E8ECF4; border-radius: 12px;
    padding: 22px 18px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.kpi-value { font-size: 2rem; font-weight: 800; color: #003399; line-height: 1.1; }
.kpi-label { font-size: 0.8rem; color: #6B7280; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.03em; }
.kpi-delta { font-size: 0.78rem; margin-top: 6px; font-weight: 600; }
.kpi-delta.pos { color: #059669; }
.kpi-delta.neg { color: #DC2626; }

.insight-box {
    background: linear-gradient(135deg, #003399 0%, #0052CC 100%);
    color: white; border-radius: 12px; padding: 22px 26px; margin: 12px 0;
}
.insight-box .ib-title { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.85; margin-bottom: 8px; }
.insight-box .ib-body { font-size: 0.95rem; line-height: 1.65; opacity: 0.93; }

.rec-card {
    background: white; border-left: 4px solid #FF6600; border-radius: 0 10px 10px 0;
    padding: 16px 20px; margin: 8px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.rec-card .rc-title { font-weight: 700; color: #1A1A2E; font-size: 0.95rem; margin-bottom: 4px; }
.rec-card .rc-body { font-size: 0.88rem; color: #4B5563; line-height: 1.55; }

.score-badge { display: inline-block; padding: 3px 10px; border-radius: 16px; font-weight: 700; font-size: 0.82rem; }
.sb-high { background: #D1FAE5; color: #065F46; }
.sb-mid { background: #FEF3C7; color: #92400E; }
.sb-low { background: #FEE2E2; color: #991B1B; }

.section-divider { border: none; border-top: 2px solid #003399; margin: 24px 0 16px 0; opacity: 0.15; }

section[data-testid="stSidebar"] { background: #003399; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] span { color: white !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover { background: rgba(255,255,255,0.1); border-radius: 6px; }
</style>
"""


def kpi_card(value: str, label: str, delta: str = None, delta_pos: bool = True) -> str:
    delta_html = ""
    if delta:
        cls = "pos" if delta_pos else "neg"
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    return f"""<div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>"""


def insight_box(title: str, body: str) -> str:
    return f"""<div class="insight-box">
        <div class="ib-title">{title}</div>
        <div class="ib-body">{body}</div>
    </div>"""


def rec_card(title: str, body: str) -> str:
    return f"""<div class="rec-card">
        <div class="rc-title">{title}</div>
        <div class="rc-body">{body}</div>
    </div>"""


def score_badge(score: int) -> str:
    if score >= 70:
        cls = "sb-high"
    elif score >= 45:
        cls = "sb-mid"
    else:
        cls = "sb-low"
    return f'<span class="score-badge {cls}">{score}</span>'
