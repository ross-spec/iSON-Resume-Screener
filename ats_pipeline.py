"""
Tab 2 — ATS / Hiring Process.

A lightweight applicant tracking system: create job requisitions, then move
candidates through a hiring pipeline (Applied -> Screened -> Interview ->
Offer -> Hired / Rejected). Data persists in a local SQLite file (db.py) so
it survives across sessions.

Also offers a one-click import of the most recent Resume Screening run
(tab 1) straight into a new or existing job's pipeline, at the "Screened"
stage, carrying over each candidate's match score.
"""
import streamlit as st
import pandas as pd

import db
from theme import md_html, NAVY, RED, MUTED, score_color

db.init_db()


def _stage_badge_color(stage):
    return {
        "Applied": "#6b6890",
        "Screened": "#3d3878",
        "Interview": "#f59e0b",
        "Offer": "#3b82f6",
        "Hired": "#22c55e",
        "Rejected": "#ec3f3d",
    }.get(stage, MUTED)


def render():
    jobs = db.get_jobs()

    # ── New job requisition ────────────────────────────────────────
    with st.expander("➕ New Job Requisition", expanded=(len(jobs) == 0)):
        c1, c2, c3 = st.columns([1.4, 1, 1])
        with c1:
            new_title = st.text_input("Role title", key="ats_new_title", placeholder="e.g. Senior BPO Team Lead")
        with c2:
            new_dept = st.text_input("Department", key="ats_new_dept", placeholder="e.g. CX Operations")
        with c3:
            new_loc = st.text_input("Location", key="ats_new_loc", placeholder="e.g. Noida")
        if st.button("Create Job", key="ats_create_job"):
            if new_title.strip():
                db.add_job(new_title, new_dept, new_loc)
                st.success(f"Created job requisition: {new_title}")
                st.rerun()
            else:
                st.warning("Role title is required.")

    if not jobs:
        st.info("No job requisitions yet. Create one above to start building a hiring pipeline.")
        return

    # ── Import from last Resume Screening run ──────────────────────
    last_screening = st.session_state.get("last_screening")
    if last_screening and last_screening.get("results"):
        with st.expander("📥 Import candidates from last Resume Screening run", expanded=False):
            st.caption(f"Last JD screened: \u201c{last_screening['jd_snippet']}...\u201d "
                       f"· {len(last_screening['results'])} candidates ranked")
            target_options = ["— Create a new job —"] + [f"{j['title']} (#{j['id']})" for j in jobs]
            target = st.selectbox("Import into", target_options, key="ats_import_target")
            new_job_title_for_import = ""
            if target == "— Create a new job —":
                new_job_title_for_import = st.text_input(
                    "New job title for imported candidates", key="ats_import_new_title",
                    placeholder="e.g. Role from latest screening run"
                )
            if st.button("Import as 'Screened' candidates", key="ats_import_btn"):
                if target == "— Create a new job —":
                    if not new_job_title_for_import.strip():
                        st.warning("Give the new job a title first.")
                        st.stop()
                    db.add_job(new_job_title_for_import, "", "")
                    job_id = db.get_jobs()[0]["id"]  # most recently created
                else:
                    job_id = int(target.split("#")[-1].rstrip(")"))
                for name, composite, semantic, years in last_screening["results"]:
                    db.add_candidate(
                        job_id, name, source="Resume Screening",
                        match_score=composite, stage="Screened",
                        notes=f"Imported from Resume Screening \u2014 JD match {semantic}%, ~{years:g} yrs experience."
                    )
                st.success(f"Imported {len(last_screening['results'])} candidates.")
                st.rerun()

    # ── Job selector ─────────────────────────────────────────────
    st.markdown('<div class="sec-h">🗂 Hiring Pipeline</div>', unsafe_allow_html=True)
    job_labels = {f"{j['title']} — {j['department'] or 'No dept'} ({j['status']})": j for j in jobs}
    selected_label = st.selectbox("Select job requisition", list(job_labels.keys()), key="ats_job_select")
    job = job_labels[selected_label]

    jc1, jc2, jc3 = st.columns([2, 1, 1])
    with jc2:
        new_status = st.selectbox("Job status", ["Open", "On Hold", "Closed"],
                                   index=["Open", "On Hold", "Closed"].index(job["status"]) if job["status"] in ["Open", "On Hold", "Closed"] else 0,
                                   key=f"ats_job_status_{job['id']}")
        if new_status != job["status"]:
            db.set_job_status(job["id"], new_status)
            st.rerun()
    with jc3:
        if st.button("🗑 Delete this job", key=f"ats_del_job_{job['id']}"):
            db.delete_job(job["id"])
            st.rerun()

    candidates = db.get_candidates(job["id"])

    # ── Pipeline metrics ─────────────────────────────────────────
    m_cols = st.columns(len(db.STAGES))
    for i, stage in enumerate(db.STAGES):
        count = sum(1 for c in candidates if c["stage"] == stage)
        m_cols[i].metric(stage, count)

    # ── Add candidate manually ──────────────────────────────────
    with st.expander("➕ Add Candidate to this Pipeline"):
        ac1, ac2, ac3, ac4 = st.columns([1.2, 1, 1, 0.8])
        with ac1:
            cand_name = st.text_input("Name", key="ats_cand_name")
        with ac2:
            cand_email = st.text_input("Email", key="ats_cand_email")
        with ac3:
            cand_phone = st.text_input("Phone", key="ats_cand_phone")
        with ac4:
            cand_stage = st.selectbox("Stage", db.STAGES, key="ats_cand_stage")
        if st.button("Add Candidate", key="ats_add_cand_btn"):
            if cand_name.strip():
                db.add_candidate(job["id"], cand_name, cand_email, cand_phone,
                                  source="Manual", stage=cand_stage)
                st.success(f"Added {cand_name} to {cand_stage}.")
                st.rerun()
            else:
                st.warning("Candidate name is required.")

    # ── Kanban board ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    board_cols = st.columns(len(db.STAGES))
    for i, stage in enumerate(db.STAGES):
        stage_candidates = [c for c in candidates if c["stage"] == stage]
        with board_cols[i]:
            badge = _stage_badge_color(stage)
            st.markdown(md_html(f"""
            <div class="stage-col-title">
                <span>{stage}</span>
                <span class="stage-count">{len(stage_candidates)}</span>
            </div>
            """), unsafe_allow_html=True)

            for cand in stage_candidates:
                score_txt = f"{cand['match_score']:.0f}%" if cand["match_score"] is not None else "—"
                st.markdown(md_html(f"""
                <div class="ats-card">
                    <div class="ats-card-name">{cand['name']}</div>
                    <div class="ats-card-meta">
                        {cand['email'] or 'no email'}{' · ' + cand['phone'] if cand['phone'] else ''}
                    </div>
                    <div class="ats-card-meta" style="margin-top:.3rem;color:{badge};font-weight:600">
                        Match score: {score_txt} · via {cand['source']}
                    </div>
                </div>
                """), unsafe_allow_html=True)

                move_to = st.selectbox(
                    "Move to", db.STAGES, index=db.STAGES.index(stage),
                    key=f"ats_move_{cand['id']}", label_visibility="collapsed"
                )
                if move_to != stage:
                    db.update_stage(cand["id"], move_to)
                    st.rerun()

                with st.popover("📝 Notes", use_container_width=True):
                    note_val = st.text_area("Notes", value=cand["notes"] or "", key=f"ats_notes_{cand['id']}",
                                             label_visibility="collapsed", height=100)
                    ncol1, ncol2 = st.columns(2)
                    with ncol1:
                        if st.button("Save", key=f"ats_save_notes_{cand['id']}"):
                            db.update_notes(cand["id"], note_val)
                            st.rerun()
                    with ncol2:
                        if st.button("🗑 Remove", key=f"ats_del_cand_{cand['id']}"):
                            db.delete_candidate(cand["id"])
                            st.rerun()

    # ── Export ───────────────────────────────────────────────────
    if candidates:
        st.markdown('<div class="sec-h">📥 Export Pipeline</div>', unsafe_allow_html=True)
        df = pd.DataFrame([{
            "Candidate": c["name"], "Email": c["email"], "Phone": c["phone"],
            "Stage": c["stage"], "Match Score": c["match_score"], "Source": c["source"],
            "Notes": c["notes"], "Added": c["added_date"], "Last Updated": c["updated_date"],
        } for c in candidates])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("📥 Export Pipeline CSV", df.to_csv(index=False).encode("utf-8"),
                            f"{job['title'].replace(' ', '_')}_pipeline.csv", "text/csv",
                            key="ats_export_csv")
