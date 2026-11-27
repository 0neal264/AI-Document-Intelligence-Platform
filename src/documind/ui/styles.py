"""Single source of dashboard CSS and design tokens."""

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
    --dm-bg: #F6F7F9;
    --dm-surface: #FFFFFF;
    --dm-border: #E2E6EC;
    --dm-input-border: #D5DAE3;
    --dm-text: #14181F;
    --dm-muted: #5B6573;
    --dm-teal: #0F766E;
    --dm-teal-tint: #E3F4F1;
    --dm-amber: #B45309;
    --dm-amber-tint: #FEF3C7;
    --dm-amber-fill: #F2B35E;
    --dm-empty: #DDE2EA;
    --dm-failed: #B42318;
    --dm-radius: 8px;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: var(--dm-bg);
    color: var(--dm-text);
    font-family: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { right: 1rem; }
.block-container { max-width: 1600px; padding: 1.5rem 2.5rem 2rem; }
[data-testid="stSidebar"] { background: var(--dm-surface); border-right: 1px solid var(--dm-border); }
[data-testid="stSidebar"] > div { background: var(--dm-surface); }

:focus-visible, button:focus-visible, a:focus-visible, input:focus-visible,
textarea:focus-visible, [role="combobox"]:focus-visible {
    outline: 2px solid var(--dm-teal) !important;
    outline-offset: 2px !important;
}
.dm-wordmark { margin: 0 0 1.5rem; color: var(--dm-text); font-size: 24px; font-weight: 600; letter-spacing: -0.03em; }
.sidebar-title { color: var(--dm-text); font-size: 15px; font-weight: 600; line-height: 1.4; }
.sidebar-muted, .muted { color: var(--dm-muted); }
.sidebar-muted { margin-top: 0.25rem; font-size: 14px; line-height: 1.45; }
.sidebar-heading { margin: 1.6rem 0 0.65rem; color: var(--dm-text); font-size: 14px; font-weight: 600; }
.coverage-map { display: grid; grid-template-columns: repeat(auto-fill, minmax(30px, 1fr)); gap: 5px; }
.coverage-cell { display: grid; aspect-ratio: 1; place-items: center; border-radius: 4px; background: var(--dm-teal); color: var(--dm-surface); font-size: 11px; }
.coverage-cell.low_text { background: var(--dm-amber-fill); color: var(--dm-text); }
.coverage-cell.empty { background: var(--dm-empty); color: var(--dm-text); }
.coverage-cell.failed { background: var(--dm-failed); color: var(--dm-surface); font-weight: 600; }
.coverage-status { margin: 0.4rem 0 0.9rem; color: var(--dm-muted); font-size: 12px; }
.sidebar-heading + div[data-testid="stRadio"] label { padding: 0.35rem 0.5rem; border-radius: var(--dm-radius); }
.sidebar-heading + div[data-testid="stRadio"] label:has(input:checked) { background: var(--dm-teal-tint); color: var(--dm-teal); font-weight: 600; }

.section-title { margin: 0 0 1rem; color: var(--dm-text); font-size: 20px; font-weight: 600; }
div[data-testid="stTabs"] button[role="tab"] { color: var(--dm-muted); font-size: 14px; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--dm-teal); border-bottom: 2px solid var(--dm-teal); }
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] [role="combobox"] { border: 1px solid var(--dm-input-border); border-radius: var(--dm-radius); background: var(--dm-surface); color: var(--dm-text); }
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button { border: 1px solid var(--dm-border); border-radius: var(--dm-radius); }
div[data-testid="stButton"] button[kind="primary"] { background: var(--dm-teal); border-color: var(--dm-teal); color: var(--dm-surface); }
div[data-testid="stExpander"] { border: 1px solid var(--dm-border); border-radius: var(--dm-radius); background: var(--dm-surface); }
div[data-testid="stAlert"] { border-radius: var(--dm-radius); }

.table-scroll { overflow-x: auto; border: 1px solid var(--dm-border); border-radius: var(--dm-radius); background: var(--dm-surface); }
.facts-table { min-width: 700px; }
.facts-head, .fact-grid-row { display: grid; grid-template-columns: minmax(260px, 3fr) minmax(120px, 1fr) minmax(70px, .6fr) minmax(110px, .8fr); gap: 1rem; align-items: center; padding: 0.75rem 1rem; }
.facts-head { color: var(--dm-muted); font-size: 13px; font-weight: 600; border-bottom: 1px solid var(--dm-border); }
.fact-grid-row { position: relative; min-height: 54px; color: var(--dm-text); font-size: 15px; border-bottom: 1px solid var(--dm-border); }
.fact-grid-row:last-child { border-bottom: 0; }
.fact-grid-row.needs-review { background: var(--dm-amber-tint); }
.fact-grid-row.needs-review::before { position: absolute; inset: 0 auto 0 0; width: 3px; background: var(--dm-amber-fill); content: ""; }
.statement { line-height: 1.45; }
.verified-text { color: var(--dm-teal); font-weight: 600; }
.review-chip { display: inline-block; width: fit-content; padding: 0.15rem 0.45rem; border-radius: var(--dm-radius); background: var(--dm-amber-tint); color: var(--dm-amber); font-size: 12px; font-weight: 600; }
.evidence-card { margin: 0.3rem 0 0.65rem; padding: 0.75rem; border: 1px solid var(--dm-border); border-radius: var(--dm-radius); background: var(--dm-surface); }
.evidence-quote { color: var(--dm-text); line-height: 1.55; }
.evidence-meta { display: flex; align-items: center; gap: 0.7rem; margin-top: 0.5rem; font-size: 13px; }
.page-badge { color: var(--dm-muted); }
mark { background: var(--dm-amber-tint); color: var(--dm-text); }
.dm-footer { margin-top: 2rem; color: var(--dm-muted); font-size: 12px; }

@media (max-width: 900px) {
    .block-container { padding: 1.25rem 1.25rem 2rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: min(100%, 320px); }
}
@media (max-width: 600px) {
    .block-container { padding: 1rem 0.75rem 1.5rem; }
    .facts-head, .fact-grid-row { gap: 0.6rem; padding: 0.65rem; }
}
</style>
"""


def dashboard_styles() -> str:
    """Return the single dashboard stylesheet for Streamlit to inject."""
    return _CSS
