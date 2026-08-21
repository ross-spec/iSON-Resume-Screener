"""
SQLite persistence layer for the ATS / Hiring Process module.

Streamlit re-runs the whole script on every interaction and doesn't keep
state between browser sessions, so job requisitions and the candidate
pipeline are stored in a local SQLite file (ats_data.db) sitting next to
the app. This means the hiring pipeline survives app restarts and is
shared by everyone using the same deployed app (e.g. the SharePoint-embedded
instance) rather than resetting per user session.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ats_data.db")

STAGES = ["Applied", "Screened", "Interview", "Offer", "Hired", "Rejected"]


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT,
            location TEXT,
            status TEXT DEFAULT 'Open',
            created_date TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            source TEXT,
            match_score REAL,
            stage TEXT DEFAULT 'Applied',
            notes TEXT,
            added_date TEXT,
            updated_date TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── Jobs ─────────────────────────────────────────────────────────────
def add_job(title, department, location):
    conn = get_conn()
    conn.execute(
        "INSERT INTO jobs (title, department, location, status, created_date) VALUES (?, ?, ?, 'Open', ?)",
        (title.strip(), department.strip(), location.strip(), _now())
    )
    conn.commit()
    conn.close()


def get_jobs(status=None):
    conn = get_conn()
    if status:
        rows = conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY created_date DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_job_status(job_id, status):
    conn = get_conn()
    conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()


def delete_job(job_id):
    conn = get_conn()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


# ── Candidates ───────────────────────────────────────────────────────
def add_candidate(job_id, name, email="", phone="", source="Manual", match_score=None, stage="Applied", notes=""):
    conn = get_conn()
    conn.execute(
        """INSERT INTO candidates
           (job_id, name, email, phone, source, match_score, stage, notes, added_date, updated_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (job_id, name.strip(), email.strip(), phone.strip(), source, match_score, stage, notes, _now(), _now())
    )
    conn.commit()
    conn.close()


def get_candidates(job_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM candidates WHERE job_id = ? ORDER BY match_score DESC", (job_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_candidates():
    conn = get_conn()
    rows = conn.execute("""
        SELECT c.*, j.title AS job_title FROM candidates c
        JOIN jobs j ON j.id = c.job_id
        ORDER BY c.updated_date DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_stage(candidate_id, stage):
    conn = get_conn()
    conn.execute("UPDATE candidates SET stage = ?, updated_date = ? WHERE id = ?", (stage, _now(), candidate_id))
    conn.commit()
    conn.close()


def update_notes(candidate_id, notes):
    conn = get_conn()
    conn.execute("UPDATE candidates SET notes = ?, updated_date = ? WHERE id = ?", (notes, _now(), candidate_id))
    conn.commit()
    conn.close()


def delete_candidate(candidate_id):
    conn = get_conn()
    conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    conn.commit()
    conn.close()
