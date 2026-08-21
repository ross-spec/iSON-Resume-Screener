"""
Shared iSON Xperiences theme — colors, CSS, and small helpers used by every
tab in the app (Resume Screening, ATS / Hiring Process, and future modules
like Payroll).
"""

NAVY = "#27235e"
NAVY_LIGHT = "#3d3878"
RED = "#ec3f3d"
BG = "#ffffff"          # white background
CARD_BG = "#f4f3fa"     # very light navy-tinted card background
TEXT = "#27235e"        # navy text for contrast on white
MUTED = "#6b6890"

GREEN = "#22c55e"
AMBER = "#f59e0b"


def md_html(text: str) -> str:
    """
    Fully left-align every line of an HTML block before passing it to
    st.markdown(). Without this, HTML written inside indented Python
    blocks (functions, if-statements, loops) keeps that Python
    indentation in the string — and Streamlit's underlying Markdown
    parser treats any line indented 4+ spaces as a literal code block
    instead of rendering it as HTML, causing raw tags to show on screen.
    """
    return "\n".join(line.lstrip() for line in text.strip("\n").split("\n"))


def score_color(s):
    if s >= 70:
        return GREEN
    if s >= 45:
        return AMBER
    return RED


GLOBAL_CSS = md_html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"] {{ background-color: {BG} !important; }}
.stApp > header {{ background-color: transparent !important; }}
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {{ background-color: transparent !important; }}
html, body, .stApp, p, span, div, label, li {{
    font-family: 'Poppins', sans-serif;
    color: {TEXT} !important;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stDeployButton"] {{ display: none !important; }}
.block-container {{ padding: 2rem 2.8rem 4rem !important; max-width: 1300px !important; }}

@media (max-width: 768px) {{
    .block-container {{ padding: 1rem 1rem 3rem !important; }}
    .hero-title {{ font-size: 1.8rem !important; }}
    .cand-card {{ padding: 1rem !important; }}
}}

/* ── TABS ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    gap: .5rem;
    border-bottom: 1px solid rgba(236,63,61,0.15) !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: 'Poppins', sans-serif !important; font-weight: 600 !important;
    font-size: .95rem !important; color: {MUTED} !important;
    padding: .6rem 1.2rem !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {RED} !important;
    border-bottom: 2px solid {RED} !important;
}}

/* ── METRIC TILES ── */
[data-testid="stMetric"] {{
    background: {CARD_BG} !important;
    border: 1px solid rgba(236,63,61,0.20) !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.4rem !important;
}}
[data-testid="stMetricLabel"] {{
    font-family: 'DM Mono', monospace !important;
    font-size: .68rem !important; letter-spacing: .12em !important;
    text-transform: uppercase !important; color: {RED} !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Poppins', sans-serif !important;
    font-weight: 800 !important; color: {NAVY} !important;
}}

/* ── BUTTONS ── */
.stButton > button {{
    font-family: 'Poppins', sans-serif !important; font-weight: 700 !important;
    border-radius: 10px !important;
    background: linear-gradient(120deg, {RED}, #c92e2c) !important;
    color: #ffffff !important; border: none !important;
    padding: .6rem 1.8rem !important; transition: all .2s !important;
}}
.stButton > button:hover {{
    opacity: .9 !important; transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(236,63,61,0.30) !important;
}}
[data-testid="stDownloadButton"] > button {{
    background: transparent !important;
    border: 1px solid rgba(236,63,61,0.35) !important;
    color: {RED} !important;
}}

/* ── INPUTS ── */
input, textarea, select,
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{
    background: {CARD_BG} !important;
    border: 1px solid rgba(236,63,61,0.22) !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
    -webkit-text-fill-color: {TEXT} !important;
    font-family: 'DM Mono', monospace !important;
}}
input:focus, textarea:focus {{
    border-color: rgba(236,63,61,0.55) !important;
    box-shadow: 0 0 0 2px rgba(236,63,61,0.10) !important;
}}
[data-baseweb="select"] > div {{
    background: {CARD_BG} !important;
    border: 1px solid rgba(236,63,61,0.22) !important;
    border-radius: 10px !important;
}}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {{
    background: rgba(0,0,0,0.2) !important;
    border: 1px dashed rgba(236,63,61,0.35) !important;
    border-radius: 12px !important; padding: .4rem !important;
}}
[data-testid="stFileUploader"] button {{
    background: linear-gradient(120deg, {RED}, #c92e2c) !important;
    color: #ffffff !important; border: none !important;
    font-family: 'Poppins', sans-serif !important; font-weight: 700 !important;
}}

/* ── DATAFRAME / ALERTS ── */
[data-testid="stDataFrame"] {{ border-radius: 12px !important; overflow: hidden; border: 1px solid rgba(236,63,61,0.12) !important; }}
[data-testid="stAlert"] {{
    background: rgba(236,63,61,0.06) !important;
    border: 1px solid rgba(236,63,61,0.20) !important;
    border-radius: 10px !important;
}}
.stSpinner > div {{ border-top-color: {RED} !important; }}
hr {{ border-color: rgba(236,63,61,0.10) !important; }}

/* ── EXPANDER ── */
[data-testid="stExpander"] {{
    background: {CARD_BG} !important;
    border: 1px solid rgba(236,63,61,0.15) !important;
    border-radius: 12px !important;
}}

/* ── REUSABLE CLASSES ── */
.sec-h {{
    font-family: 'Poppins', sans-serif !important; font-size: 1.25rem !important;
    font-weight: 700 !important; color: {NAVY} !important;
    display: flex; align-items: center; gap: .6rem;
    margin: 2.2rem 0 1rem; padding: .4rem 0;
}}
.sec-h::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(236,63,61,.35), transparent);
    margin-left: .4rem;
}}
.cand-card {{
    background: {CARD_BG}; border: 1px solid rgba(236,63,61,0.12);
    border-radius: 16px; padding: 1.5rem 1.8rem; margin-bottom: 1.2rem;
}}
.skills-block, .rec-block {{
    background: rgba(0,0,0,0.2); border-radius: 10px; padding: .9rem 1.1rem;
    font-family: 'DM Mono', monospace; font-size: .78rem; color: {MUTED}; line-height: 1.75; margin-top: .4rem;
}}
.block-title {{
    font-family: 'DM Mono', monospace; font-size: .63rem; text-transform: uppercase;
    letter-spacing: .16em; color: {MUTED}; margin-bottom: .35rem;
}}
.sbar-bg {{ background: rgba(255,255,255,0.06); border-radius: 999px; height: 6px; overflow: hidden; }}
.sbar-fill {{ height: 100%; border-radius: 999px; }}
.exp-pill {{
    display:inline-block; font-family:'DM Mono',monospace; font-size:.7rem;
    background: rgba(39,35,94,0.08); color: {NAVY}; border-radius: 999px;
    padding: .2rem .7rem; margin-left:.5rem;
}}

/* ── ATS KANBAN ── */
.stage-col-title {{
    font-family: 'Poppins', sans-serif; font-weight: 700; font-size: .82rem;
    color: {NAVY}; text-transform: uppercase; letter-spacing: .04em;
    padding: .5rem .2rem; border-bottom: 2px solid rgba(236,63,61,0.25);
    margin-bottom: .8rem; display:flex; justify-content:space-between; align-items:center;
}}
.stage-count {{
    font-family:'DM Mono',monospace; font-size:.7rem; color:{RED};
    background: rgba(236,63,61,0.10); border-radius:999px; padding:.05rem .55rem;
}}
.ats-card {{
    background: {CARD_BG}; border: 1px solid rgba(236,63,61,0.14);
    border-radius: 12px; padding: .85rem 1rem; margin-bottom: .7rem;
}}
.ats-card-name {{
    font-family:'Poppins',sans-serif; font-weight:700; font-size:.88rem; color:{NAVY};
}}
.ats-card-meta {{
    font-family:'DM Mono',monospace; font-size:.68rem; color:{MUTED}; margin-top:.15rem;
}}
.job-pill {{
    display:inline-block; font-family:'DM Mono',monospace; font-size:.68rem;
    background: rgba(236,63,61,0.10); color:{RED}; border-radius:999px;
    padding:.15rem .6rem; margin-right:.4rem;
}}
</style>
""")
