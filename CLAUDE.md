# FUEL-INTEL — Reliance Fuel & EV Location Intelligence Platform

## Project Overview
A CEO-grade decision-support dashboard for identifying optimal locations for fuel retail and EV supercharger stations across India. Built with Streamlit, deployed to Streamlit Community Cloud.

## Architecture Rules (NEVER violate)
- Streamlit is the ONLY frontend. No Flask, FastAPI, Django, or React.
- Python is the ONLY language. No JavaScript computation logic.
- Plotly graph_objects for ALL charts. Not matplotlib, not altair, not plotly.express. graph_objects gives CEO-grade control over every visual element.
- folium + streamlit-folium for the heat map. Not pydeck, not kepler, not deck.gl.
- All monetary values displayed in ₹ Crores unless explicitly stated otherwise.
- pandas for all data manipulation. No polars, no dask.
- pydantic for all config/settings validation.

## Data Integrity Rules (CRITICAL)
- Every data source MUST be registered in data/registry.py with: source_id, source_name, source_url, provider, last_updated, update_frequency, license, description, records_loaded, quality_notes.
- Never silently drop rows or columns. If a parse fails, log a warning AND surface it in the Architecture tab under "Data Quality Warnings."
- All seed CSV files MUST start with a comment header: # Source: [URL] | Downloaded: [date] | Coverage: [description]
- Uploaded user data MUST be validated before merging. Reject files missing required columns with a clear st.error message listing what's missing.
- When a data source has no API, the seed data is the fallback. The Architecture tab must show "Using seed data (may be outdated)" with a 🟡 indicator.

## Scoring Model Rules (NEVER deviate)
- 6 pillars: demand, competition, income, ev_readiness, infrastructure, growth_trajectory.
- Weights MUST sum to 1.0. If user-provided weights don't sum to 1.0, normalize them silently.
- Competition pillar is INVERTED before weighting: competition_score = 100 - raw_competition_value. Low raw competition = high opportunity = high score.
- All pillar scores are 0-100. Composite score is 0-100.
- Score tiers: "High Potential" >= 70, "Moderate" 45-69, "Low Potential" < 45.

## Profitability Model Rules
- Discount rate: 12% (India WACC benchmark). Configurable in settings.py but default is 12%.
- NPV horizon: 15 years. Non-negotiable for the default view.
- EV transition: fuel volume declines 2% annually starting year 5. EV revenue grows on logistic S-curve (15% annual growth, capped at saturation).
- Breakeven must be <= 15 years. If > 15, flag as "Not viable within planning horizon."
- CAPEX by format: Large Highway ₹22Cr, Urban Full-Service ₹18Cr, EV-Focused ₹15Cr, Hybrid ₹12Cr, Compact ₹8Cr.

## Format Recommendation Decision Tree
Priority order (first match wins):
1. LARGE HIGHWAY HUB: tier == "highway" AND demand > 55 AND competition < 40
2. EV-FOCUSED STATION: ev_readiness > 65 AND income > 70 AND tier in ("metro", "emerging")
3. URBAN FULL-SERVICE: tier in ("metro", "emerging") AND demand > 70 AND income > 65
4. COMPACT URBAN: demand < 55 OR (tier == "tier3" AND composite_score < 45)
5. HYBRID TRANSITION: everything else (default)

## UI / CEO Dashboard Standards (ENFORCE STRICTLY)
- NO developer jargon anywhere in the UI. "Location Attractiveness Score" not "LAS". "Financial Return" not "NPV" (show NPV as the number, but label it "15-Year Net Value").
- Every metric MUST have context: what it means, whether it's good/bad, and what action to take.
- Every chart MUST have: a title, axis labels, and a one-line insight caption below it.
- Executive Summary loads first. Always. It's the landing page.
- Reliance brand palette: primary #003399 (deep blue), accent #FF6600 (orange), success #059669 (green), warning #D97706 (amber), danger #DC2626 (red), background #FAFBFE, text #1A1A2E.
- Font: Inter (imported from Google Fonts via CSS).
- White space is a feature. Never cram. Use st.columns with spacing.
- No Streamlit default hamburger menu or footer. Hide with CSS.

## Testing Rules
- Every scoring function must have a hand-verified test case with known expected output.
- Profitability model sanity: Mumbai metro NPV > Tier-3 rural NPV. Always.
- All data parsers must handle empty input, malformed input, and missing columns without crashing.
- Run pytest before every git commit.

## Terminal / Shell Rules (macOS zsh)
- One command at a time. Never batch commands with &&.
- No inline # comments in shell commands — zsh chokes on them.
- Always cd into ~/projects/fuel-intel before running any command.
- Always activate venv: source .venv/bin/activate
- Working directory for all operations: ~/projects/fuel-intel

## File Organization
- app.py is the single Streamlit entry point. No multi-page app structure via pages/ directory (Streamlit native). All routing via sidebar radio buttons inside app.py.
- config/ for settings, assumptions, constants.
- core/ for scoring, format recommendation, profitability — pure logic, no UI.
- data/ for ingestion, seed CSVs, uploads, registry.
- ui/ for all Streamlit rendering code — pages/ for page renderers, components/ for reusable widgets.
- utils/ for formatters, geo helpers, validators.
- tests/ for pytest test files.

## Dependencies (requirements.txt is the source of truth)
streamlit, plotly, folium, streamlit-folium, pandas, numpy, scipy, requests, openpyxl, pydantic, python-dateutil, geopy, branca

## Git Discipline
- .gitignore must exclude: __pycache__, .venv, .env, data/uploads/*, .DS_Store
- data/seed/ is tracked (small CSVs).
- data/uploads/ has only .gitkeep tracked.
- Commit messages: "v[X.Y.Z] — [short description]"
