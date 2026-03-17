"""
SQLite-backed job queue storage.

Provides functions for managing a persistent queue of SQL query jobs
with status tracking and lifecycle management.
"""
import sqlite3
import time
import uuid
import threading
from typing import Optional

# Module-level lock for thread safety
_db_lock = threading.Lock()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id       TEXT PRIMARY KEY,
    query_text   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'queued',
    error_message TEXT,
    created_at   REAL NOT NULL,
    started_at   REAL,
    completed_at REAL
);
"""


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def init_db(db_path: str) -> str:
    """Initialize the queue database, creating the table if needed.

    Returns the db_path for convenience.
    """
    with _db_lock:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(SCHEMA_SQL)
            conn.commit()
        finally:
            conn.close()
    return db_path


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return uuid.uuid4().hex[:12]


def insert_job(db_path: str, job_id: str, query_text: str) -> dict:
    """Insert a new job into the queue with 'queued' status.

    Returns the created job as a dict.
    """
    now = time.time()
    with _db_lock:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute(
                "INSERT INTO jobs (job_id, query_text, status, created_at) VALUES (?, ?, 'queued', ?)",
                (job_id, query_text, now),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            return _row_to_dict(row)
        finally:
            conn.close()


def claim_next_job(db_path: str) -> Optional[dict]:
    """Atomically claim the oldest queued job by setting it to 'running'.

    Uses UPDATE ... RETURNING for atomicity (SQLite 3.35+).
    Returns the claimed job dict, or None if no queued jobs.
    """
    now = time.time()
    with _db_lock:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            # Find the oldest queued job and atomically update it
            row = conn.execute(
                """
                UPDATE jobs
                SET status = 'running', started_at = ?
                WHERE job_id = (
                    SELECT job_id FROM jobs
                    WHERE status = 'queued'
                    ORDER BY created_at ASC
                    LIMIT 1
                )
                RETURNING *
                """,
                (now,),
            ).fetchone()
            conn.commit()
            return _row_to_dict(row) if row else None
        finally:
            conn.close()


def update_job_status(
    db_path: str,
    job_id: str,
    status: str,
    error_message: Optional[str] = None,
) -> dict:
    """Update a job's status and optionally set an error message.

    Sets completed_at for terminal states (succeeded, failed).
    Returns the updated job dict.
    """
    now = time.time()
    with _db_lock:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            if status in ("succeeded", "failed"):
                conn.execute(
                    "UPDATE jobs SET status = ?, error_message = ?, completed_at = ? WHERE job_id = ?",
                    (status, error_message, now, job_id),
                )
            else:
                conn.execute(
                    "UPDATE jobs SET status = ?, error_message = ? WHERE job_id = ?",
                    (status, error_message, job_id),
                )
            conn.commit()
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            return _row_to_dict(row)
        finally:
            conn.close()


def get_job(db_path: str, job_id: str) -> Optional[dict]:
    """Retrieve a single job by ID. Returns None if not found."""
    with _db_lock:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            return _row_to_dict(row) if row else None
        finally:
            conn.close()


def list_jobs(db_path: str) -> list[dict]:
    """List all jobs ordered by created_at descending (newest first)."""
    with _db_lock:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
            return [_row_to_dict(r) for r in rows]
        finally:
            conn.close()


def cleanup_old_jobs(db_path: str, max_jobs: int = 50) -> list[str]:
    """Delete the oldest jobs beyond the max_jobs cap.

    Returns a list of deleted job_ids so callers can clean up
    associated resources (e.g., result cache tables).
    """
    with _db_lock:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            # Find jobs to delete (oldest beyond the cap)
            rows = conn.execute(
                """
                SELECT job_id FROM jobs
                WHERE job_id NOT IN (
                    SELECT job_id FROM jobs
                    ORDER BY created_at DESC
                    LIMIT ?
                )
                """,
                (max_jobs,),
            ).fetchall()

            deleted_ids = [r["job_id"] for r in rows]

            if deleted_ids:
                placeholders = ",".join("?" for _ in deleted_ids)
                conn.execute(f"DELETE FROM jobs WHERE job_id IN ({placeholders})", deleted_ids)
                conn.commit()

            return deleted_ids
        finally:
            conn.close()
