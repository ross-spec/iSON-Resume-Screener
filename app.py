import streamlit as st
import os
import base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import PyPDF2
import docx2txt
from sentence_transformers import SentenceTransformer, util

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="iSON Xperiences | Resume Screening Tool",
    page_icon="assets/logo.png" if os.path.isfile("assets/logo.png") else "📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════
# BRAND COLORS — sampled directly from the iSON Xperiences logo
# ══════════════════════════════════════════════════════════════════════
NAVY = "#27235e"
NAVY_LIGHT = "#3d3878"
RED = "#ec3f3d"
BG = "#0e0c22"          # dark navy background derived from NAVY
CARD_BG = "#171438"
TEXT = "#e8e8f0"
MUTED = "#8a87ad"

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS — iSON Xperiences theme (navy + red)
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
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
    font-weight: 800 !important; color: #ffffff !important;
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
input, textarea, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {{
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

/* ── REUSABLE CLASSES ── */
.sec-h {{
    font-family: 'Poppins', sans-serif !important; font-size: 1.25rem !important;
    font-weight: 700 !important; color: #ffffff !important;
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
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# OPTIONAL AI HELPERS (skill extraction / hiring notes)
# Only active if an OPENROUTER_API_KEY is configured in Streamlit secrets.
# The core resume-vs-JD matching below does NOT require this — it runs
# fully on the local sentence-transformers model either way.
# ══════════════════════════════════════════════════════════════════════
def ai_available():
    try:
        return bool(st.secrets.get("OPENROUTER_API_KEY"))
    except Exception:
        return False


def call_ai(prompt: str) -> str:
    import requests
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                     "Content-Type": "application/json"},
            json={"model": "openai/gpt-4o-mini",
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.2}
        )
        return r.json()["choices"][0]["message"]["content"] if r.status_code == 200 else "AI service unavailable."
    except Exception as ex:
        return f"AI error: {ex}"


def extract_skills(text):
    return call_ai(f"""
Extract the top 8-10 professional skills from this resume.
Return ONLY a clean bullet list, no preamble.
Resume: {text[:2500]}
""")


def generate_recommendation(jd, resume, score):
    return call_ai(f"""
You are a senior hiring manager. Analyse this candidate concisely.
Match Score: {score}%
Job Description: {jd[:1200]}
Resume: {resume[:1800]}
Return three short sections:
STRENGTHS (2-3 bullets)
GAPS (2-3 bullets)
RECOMMENDATION (1 sentence: Hire / Maybe / Skip + reason)
""")


# ══════════════════════════════════════════════════════════════════════
# CORE MATCHING LOGIC (offline — sentence-transformers)
# ══════════════════════════════════════════════════════════════════════
@st.cache_resource
def load_embed_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def extract_text(file) -> str:
    ext = os.path.splitext(file.name)[1].lower()
    if ext == ".pdf":
        reader = PyPDF2.PdfReader(file)
        return "".join(p.extract_text() or "" for p in reader.pages)
    elif ext == ".docx":
        return docx2txt.process(file)
    return ""


def compute_similarity(resume_texts, jd_text):
    model = load_embed_model()
    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    out = []
    for name, text in resume_texts:
        if not text.strip():
            out.append((name, text, 0.0))
            continue
        emb = model.encode(text, convert_to_tensor=True)
        score = round(util.cos_sim(jd_emb, emb).item() * 100, 1)
        out.append((name, text, score))
    return sorted(out, key=lambda x: x[2], reverse=True)


def score_color(s):
    if s >= 70:
        return "#22c55e"
    if s >= 45:
        return "#f59e0b"
    return RED


# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════
def render_header():
    logo_html = ""
    if os.path.isfile("assets/logo.png"):
        with open("assets/logo.png", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}" style="height:52px;margin-bottom:1rem" />'

    st.markdown(f"""
    <div style="text-align:center;padding:2.5rem 0 1.5rem">
        {logo_html}
        <h1 class="hero-title" style="font-family:'Poppins',sans-serif;font-size:clamp(1.8rem,4vw,2.6rem);
                   font-weight:800;letter-spacing:-.02em;color:#ffffff;margin:0 0 .5rem">
            Resume Screening Tool
        </h1>
        <p style="font-family:'DM Mono',monospace;font-size:.85rem;color:{MUTED};margin:0">
            Internal HR tool · Upload resumes, paste a job description, get ranked matches
        </p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════
render_header()

col_hero, col_panel = st.columns([1, 1.15], gap="large")

with col_hero:
    st.markdown(f"""
    <div style="padding:1rem 0">
        <p style="font-family:'DM Mono',monospace;font-size:.75rem;color:{RED};
                  letter-spacing:.1em;text-transform:uppercase;margin-bottom:.6rem">
            How it works
        </p>
        <p style="font-family:'Poppins',sans-serif;font-size:.95rem;color:{MUTED};line-height:1.8">
            1. Upload candidate resumes (PDF or DOCX)<br>
            2. Paste the job description for the role<br>
            3. Click Analyze — candidates are ranked by AI semantic match<br>
            4. Export the ranked list to CSV to share with the hiring team
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_panel:
    st.markdown('<p class="block-title">📂 Resume Upload (PDF / DOCX)</p>', unsafe_allow_html=True)
    resume_files = st.file_uploader("Resumes", type=["pdf", "docx"],
                                     accept_multiple_files=True, label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="block-title">📝 Job Description</p>', unsafe_allow_html=True)
    jd_input = st.text_area("JD", height=180, label_visibility="collapsed",
                             placeholder="Paste the full job description here...")
    st.markdown("<br>", unsafe_allow_html=True)
    analyze = st.button("⚡  Analyze Candidates", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════
if analyze:
    if not resume_files or not jd_input.strip():
        st.warning("Please upload at least one resume and provide a job description.")
        st.stop()

    with st.spinner("Running semantic AI analysis..."):
        resume_texts = [(f.name, extract_text(f)) for f in resume_files]
        results = compute_similarity(resume_texts, jd_input)

    scores = [r[2] for r in results]
    avg_score = round(float(np.mean(scores)), 1)
    top_score = max(scores)

    st.markdown('<div class="sec-h">📊 Screening Dashboard</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Resumes Uploaded", len(resume_files))
    k2.metric("Candidates Ranked", len(results))
    k3.metric("Top Match Score", f"{top_score}%")
    k4.metric("Avg Match Score", f"{avg_score}%")

    top = results[0]
    col = score_color(top[2])
    st.markdown(f"""
    <div style="background:linear-gradient(120deg,rgba(236,63,61,0.10),rgba(39,35,94,0.25));
                border:1px solid rgba(236,63,61,0.25);border-radius:14px;
                padding:1.2rem 1.6rem;display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem">
        <div style="font-size:2rem">🏆</div>
        <div>
            <div style="font-family:'Poppins',sans-serif;font-size:1.2rem;font-weight:700;color:{col}">{top[0]}</div>
            <div style="font-family:'DM Mono',monospace;font-size:.75rem;color:{MUTED}">
                Best overall match · {top[2]}% similarity
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Score chart
    st.markdown('<div class="sec-h">📈 Match Score Comparison</div>', unsafe_allow_html=True)
    names = [r[0] for r in results]
    values = [r[2] for r in results]
    bcolors = [score_color(v) for v in values]
    fig, ax = plt.subplots(figsize=(9, max(3, len(names) * 0.6)))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(CARD_BG)
    bars = ax.barh(names, values, color=bcolors, height=0.55, zorder=3)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Match Score (%)", color=MUTED, fontsize=9, fontfamily="monospace")
    ax.tick_params(colors="#c9c7de", labelsize=9)
    ax.spines[:].set_visible(False)
    ax.xaxis.grid(True, color=(1, 1, 1, 0.05), zorder=0)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + .8, bar.get_y() + bar.get_height() / 2,
                 f"{val}%", va="center", ha="left", color="#c9c7de", fontsize=8, fontfamily="monospace")
    plt.tight_layout()
    st.pyplot(fig)

    # Ranking table + export
    st.markdown('<div class="sec-h">🗂 Candidate Ranking</div>', unsafe_allow_html=True)
    df = pd.DataFrame([(i + 1, r[0], f"{r[2]}%") for i, r in enumerate(results)],
                       columns=["Rank", "Candidate", "Match Score"])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("📥 Export CSV", df.to_csv(index=False).encode("utf-8"),
                        "candidate_ranking.csv", "text/csv")

    # Candidate deep-dive
    st.markdown('<div class="sec-h">🔬 Candidate Analysis</div>', unsafe_allow_html=True)
    for rank, (cname, text, score) in enumerate(results, 1):
        fill = int(score)
        col = score_color(score)
        st.markdown(f"""
        <div class="cand-card">
            <div style="font-family:'DM Mono',monospace;font-size:.65rem;letter-spacing:.12em;color:{MUTED}">RANK #{rank}</div>
            <div style="font-family:'Poppins',sans-serif;font-size:1.1rem;font-weight:700;color:#e8e8f0;margin:.15rem 0 .6rem">{cname}</div>
            <div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.9rem">
                <div class="sbar-bg" style="flex:1">
                    <div class="sbar-fill" style="width:{fill}%;background:linear-gradient(90deg,{col},{col}88)"></div>
                </div>
                <span style="font-family:'DM Mono',monospace;font-size:.82rem;color:{col};font-weight:600">{score}%</span>
            </div>
        """, unsafe_allow_html=True)

        if ai_available():
            with st.spinner(f"Extracting skills for {cname}..."):
                skills = extract_skills(text)
            st.markdown('<div class="block-title">🔍 Extracted Skills</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="skills-block">{skills}</div>', unsafe_allow_html=True)

            with st.spinner(f"Generating hiring notes for {cname}..."):
                rec = generate_recommendation(jd_input, text, score)
            st.markdown('<div class="block-title">🤖 AI Hiring Notes</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="rec-block">{rec}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center;margin-top:4rem;padding-top:2rem;
            border-top:1px solid rgba(236,63,61,0.08)">
    <span style="font-family:'DM Mono',monospace;font-size:.65rem;
                 letter-spacing:.1em;color:{NAVY_LIGHT}">
        iSON Xperiences · Internal HR Tool
    </span>
</div>
""", unsafe_allow_html=True)
