"""
Tab 1 — Resume Screening.
This is the existing offline resume-vs-JD matching tool, unchanged in logic,
refactored into a render() function so it can live inside a tab alongside
the ATS / Hiring Process module.
"""
import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import PyPDF2
import docx2txt
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

from theme import md_html, NAVY, RED, MUTED, CARD_BG, BG, score_color

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
# EXPERIENCE EXTRACTION (offline, regex-based — no AI/API call)
# ══════════════════════════════════════════════════════════════════════
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december"

def _spaced(word: str) -> str:
    """Builds a regex that tolerates stray whitespace between every letter of
    `word`. Some resume PDFs (especially design-tool exports like Canva) have
    embedded fonts with kerning tables that make PyPDF2 insert extra spaces
    mid-word on extraction — e.g. "years" comes out as "y ears". Without this,
    a straightforward `years?` pattern silently fails to match on those files."""
    return r'\s*'.join(list(word))

_YEAR_WORD = r'(?:' + _spaced("years") + r'|' + _spaced("year") + r')'
_YR_WORD = r'(?:' + _spaced("yrs") + r'|' + _spaced("yr") + r')'
_EXPERIENCE_WORD = _spaced("experience")
_OF_WORD = _spaced("of")
_RELEVANT_WORD = _spaced("relevant")

_EXPLICIT_PATTERN = re.compile(
    r'(\d{1,2})\+?\s*(?:' + _YEAR_WORD + r'|' + _YR_WORD + r')\s*'
    r'(?:' + _OF_WORD + r'\s*)?(?:' + _RELEVANT_WORD + r'\s*)?'
    r'(?:\w+[\s\-]+){0,3}' + _EXPERIENCE_WORD
)

_MONTH_PREFIX = r'(?:(?:' + MONTHS + r')[\s.\'\u2019]*|\d{1,2}\s*[/.\-]\s*)?'
_RANGE_SEP = r'\s*(?:-|\u2013|to)\s*'
_RANGE_PATTERN = re.compile(
    _MONTH_PREFIX + r'(\d{4})' + _RANGE_SEP + _MONTH_PREFIX + r'(\d{4}|present|current|till date|ongoing)',
    re.IGNORECASE
)

def extract_experience_years(text: str) -> float:
    """
    Estimates total years of professional experience from resume text using
    two strategies, in priority order:
      1. An explicit stated figure, e.g. "5+ years of experience",
         "8 years experience" — most reliable when present.
      2. Date ranges in a work-history section, e.g. "Jan 2019 - Present",
         "2018 - 2022", "05/2022 - 03/2026" — summed as a fallback when no
         explicit figure exists.
    Both patterns tolerate stray whitespace inserted mid-word by PyPDF2 on
    certain fonts. Purely offline (regex only) — no AI/API call, no cost.
    """
    t = text.lower()

    explicit = _EXPLICIT_PATTERN.findall(t)
    if explicit:
        return float(max(int(x) for x in explicit))

    current_year = datetime.now().year
    total_months = 0
    matches = _RANGE_PATTERN.findall(t)
    for start_year, end_year in matches:
        start_year = int(start_year)
        end_year = current_year if end_year in ("present", "current", "till date", "ongoing") else int(end_year)
        if 1970 <= start_year <= current_year and start_year <= end_year <= current_year + 1:
            total_months += (end_year - start_year) * 12

    if total_months > 0:
        return round(min(total_months / 12, 40), 1)

    return 0.0


def experience_score(years: float, cap_years: float = 10.0) -> float:
    """Converts years of experience into a 0-100 score, capped at cap_years
    so a 20-year veteran doesn't automatically dominate a role that only
    needs ~10 years — beyond the cap, more experience stops adding score."""
    return round(min(years, cap_years) / cap_years * 100, 1)


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


def compute_similarity(resume_texts, jd_text, experience_weight: float = 0.3):
    """
    Returns candidates ranked by a COMPOSITE score:
        composite = (1 - experience_weight) * semantic_match
                  +      experience_weight   * experience_score
    """
    model = load_embed_model()
    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    out = []
    for name, text in resume_texts:
        if not text.strip():
            out.append((name, text, 0.0, 0.0, 0.0))
            continue
        emb = model.encode(text, convert_to_tensor=True)
        semantic = round(util.cos_sim(jd_emb, emb).item() * 100, 1)
        years = extract_experience_years(text)
        exp_score = experience_score(years)
        composite = round((1 - experience_weight) * semantic + experience_weight * exp_score, 1)
        out.append((name, text, composite, semantic, years))
    return sorted(out, key=lambda x: x[2], reverse=True)


# ══════════════════════════════════════════════════════════════════════
# RENDER — called from app.py inside the "Resume Screening" tab
# ══════════════════════════════════════════════════════════════════════
def render():
    col_hero, col_panel = st.columns([1, 1.15], gap="large")

    with col_hero:
        st.markdown(md_html(f"""
        <div style="padding:1rem 0">
            <p style="font-family:'DM Mono',monospace;font-size:.75rem;color:{RED};
                      letter-spacing:.1em;text-transform:uppercase;margin-bottom:.6rem">
                How it works
            </p>
            <p style="font-family:'Poppins',sans-serif;font-size:.95rem;color:{MUTED};line-height:1.8">
                1. Upload candidate resumes (PDF or DOCX)<br>
                2. Paste the job description for the role<br>
                3. Click Analyze — candidates are ranked by JD match + experience<br>
                4. Export the ranked list to CSV, or send top candidates straight
                   to the ATS / Hiring Process tab
            </p>
        </div>
        """), unsafe_allow_html=True)

    with col_panel:
        st.markdown('<p class="block-title">📂 Resume Upload (PDF / DOCX)</p>', unsafe_allow_html=True)
        resume_files = st.file_uploader("Resumes", type=["pdf", "docx"],
                                         accept_multiple_files=True, label_visibility="collapsed",
                                         key="rs_resume_files")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="block-title">📝 Job Description</p>', unsafe_allow_html=True)
        jd_input = st.text_area("JD", height=180, label_visibility="collapsed",
                                 placeholder="Paste the full job description here...",
                                 key="rs_jd_input")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="block-title">⚖️ Experience Weight in Final Score</p>', unsafe_allow_html=True)
        exp_weight_pct = st.slider("Experience weight", 0, 100, 30, step=5,
                                    label_visibility="collapsed",
                                    help="How much weight years-of-experience gets vs. JD wording match. "
                                         "0% = pure semantic match. 30% = default, balanced.",
                                    key="rs_exp_weight")
        st.markdown("<br>", unsafe_allow_html=True)
        analyze = st.button("⚡  Analyze Candidates", use_container_width=True, key="rs_analyze")

    if analyze:
        if not resume_files or not jd_input.strip():
            st.warning("Please upload at least one resume and provide a job description.")
            st.stop()

        with st.spinner("Running semantic AI analysis..."):
            resume_texts = [(f.name, extract_text(f)) for f in resume_files]
            results = compute_similarity(resume_texts, jd_input, experience_weight=exp_weight_pct / 100)

        # Stash results in session_state so the ATS tab can offer a one-click
        # import of this run's candidates into a hiring pipeline.
        st.session_state["last_screening"] = {
            "jd_snippet": jd_input.strip()[:120],
            "results": [(r[0], r[2], r[3], r[4]) for r in results],  # name, composite, semantic, years
        }

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
        st.markdown(md_html(f"""
        <div style="background:linear-gradient(120deg,rgba(236,63,61,0.10),rgba(39,35,94,0.25));
                    border:1px solid rgba(236,63,61,0.25);border-radius:14px;
                    padding:1.2rem 1.6rem;display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem">
            <div style="font-size:2rem">🏆</div>
            <div>
                <div style="font-family:'Poppins',sans-serif;font-size:1.2rem;font-weight:700;color:{col}">{top[0]}</div>
                <div style="font-family:'DM Mono',monospace;font-size:.75rem;color:{MUTED}">
                    Best overall match · {top[2]}% composite (JD match {top[3]}% · ~{top[4]:g} yrs experience)
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)

        st.warning(
            "⚠️ **\"Experience (yrs)\" is an automated estimate**, detected from wording and date "
            "ranges in each resume — not a guaranteed-accurate reading. Formatting differences between "
            "resumes can cause it to under- or over-detect. Please verify actual years of experience "
            "against the resume itself before making any hiring decision based on this number."
        )

        st.markdown('<div class="sec-h">📈 Composite Score Comparison</div>', unsafe_allow_html=True)
        names = [r[0] for r in results]
        values = [r[2] for r in results]
        bcolors = [score_color(v) for v in values]
        fig, ax = plt.subplots(figsize=(9, max(3, len(names) * 0.6)))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(CARD_BG)
        bars = ax.barh(names, values, color=bcolors, height=0.55, zorder=3)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Composite Score (%)", color=MUTED, fontsize=9, fontfamily="monospace")
        ax.tick_params(colors=NAVY, labelsize=9)
        ax.spines[:].set_visible(False)
        ax.xaxis.grid(True, color=(1, 1, 1, 0.05), zorder=0)
        ax.set_axisbelow(True)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + .8, bar.get_y() + bar.get_height() / 2,
                     f"{val}%", va="center", ha="left", color=NAVY, fontsize=8, fontfamily="monospace")
        plt.tight_layout()
        st.pyplot(fig)

        st.markdown('<div class="sec-h">🗂 Candidate Ranking</div>', unsafe_allow_html=True)
        df = pd.DataFrame(
            [(i + 1, r[0], f"{r[2]}%", f"{r[3]}%", f"{r[4]:g}") for i, r in enumerate(results)],
            columns=["Rank", "Candidate", "Composite Score", "JD Match", "Experience (yrs)"]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("📥 Export CSV", df.to_csv(index=False).encode("utf-8"),
                            "candidate_ranking.csv", "text/csv", key="rs_export_csv")

        st.markdown('<div class="sec-h">🔬 Candidate Analysis</div>', unsafe_allow_html=True)
        for rank, (cname, text, composite, semantic, years) in enumerate(results, 1):
            fill = int(composite)
            col = score_color(composite)
            st.markdown(md_html(f"""
            <div class="cand-card">
                <div style="font-family:'DM Mono',monospace;font-size:.65rem;letter-spacing:.12em;color:{MUTED}">RANK #{rank}</div>
                <div style="font-family:'Poppins',sans-serif;font-size:1.1rem;font-weight:700;color:{NAVY};margin:.15rem 0 .6rem">
                    {cname}
                    <span class="exp-pill">~{years:g} yrs experience</span>
                    <span class="exp-pill">JD match {semantic}%</span>
                </div>
                <div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.9rem">
                    <div class="sbar-bg" style="flex:1">
                        <div class="sbar-fill" style="width:{fill}%;background:linear-gradient(90deg,{col},{col}88)"></div>
                    </div>
                    <span style="font-family:'DM Mono',monospace;font-size:.82rem;color:{col};font-weight:600">{composite}%</span>
                </div>
            """), unsafe_allow_html=True)

            if ai_available():
                with st.spinner(f"Extracting skills for {cname}..."):
                    skills = extract_skills(text)
                st.markdown('<div class="block-title">🔍 Extracted Skills</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="skills-block">{skills}</div>', unsafe_allow_html=True)

                with st.spinner(f"Generating hiring notes for {cname}..."):
                    rec = generate_recommendation(jd_input, text, composite)
                st.markdown('<div class="block-title">🤖 AI Hiring Notes</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="rec-block">{rec}</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
