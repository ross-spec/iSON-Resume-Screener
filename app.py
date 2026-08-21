import os
import streamlit as st

from theme import GLOBAL_CSS, md_html, NAVY, NAVY_LIGHT, MUTED
import resume_screening
import ats_pipeline

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="iSON Xperiences | HR Suite",
    page_icon="assets/logo.png" if os.path.isfile("assets/logo.png") else "🗂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════
def render_header():
    logo_html = ""
    if os.path.isfile("assets/logo.png"):
        import base64
        with open("assets/logo.png", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}" style="height:52px;margin-bottom:1rem" />'

    st.markdown(md_html(f"""
    <div style="text-align:center;padding:2.5rem 0 1.5rem">
        {logo_html}
        <h1 class="hero-title" style="font-family:'Poppins',sans-serif;font-size:clamp(1.8rem,4vw,2.6rem);
                   font-weight:800;letter-spacing:-.02em;color:{NAVY};margin:0 0 .5rem">
            HR Suite
        </h1>
        <p style="font-family:'DM Mono',monospace;font-size:.85rem;color:{MUTED};margin:0">
            Internal HR tool · Resume Screening &amp; ATS / Hiring Pipeline
        </p>
    </div>
    """), unsafe_allow_html=True)


render_header()

tab_resume, tab_ats = st.tabs(["📄 Resume Screening", "🗂 ATS / Hiring Process"])

with tab_resume:
    resume_screening.render()

with tab_ats:
    ats_pipeline.render()

st.markdown(md_html(f"""
<div style="text-align:center;margin-top:4rem;padding-top:2rem;
            border-top:1px solid rgba(236,63,61,0.08)">
    <span style="font-family:'DM Mono',monospace;font-size:.65rem;
                 letter-spacing:.1em;color:{NAVY_LIGHT}">
        iSON Xperiences · Internal HR Tool
    </span>
</div>
"""), unsafe_allow_html=True)
