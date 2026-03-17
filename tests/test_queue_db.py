"""Tests for the SQLite queue storage layer."""
import os
import time
import tempfile
import pytest

from secondmate.queue.db import (
    init_db,
    generate_job_id,
    insert_job,
    claim_next_job,
    update_job_status,
    get_job,
    list_jobs,
    cleanup_old_jobs,
)


@pytest.fixture
def db_path():
    """Create a temporary database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    init_db(path)
    yield path
    os.unlink(path)


class TestInsertJob:
    def test_insert_creates_job_with_queued_status(self, db_path):
        job_id = generate_job_id()
        job = insert_job(db_path, job_id, "SELECT 1")

        assert job["job_id"] == job_id
        assert job["query_text"] == "SELECT 1"
        assert job["status"] == "queued"
        assert job["error_message"] is None
        assert job["created_at"] is not None
        assert job["started_at"] is None
        assert job["completed_at"] is None

    def test_insert_multiple_jobs(self, db_path):
        for i in range(5):
            insert_job(db_path, generate_job_id(), f"SELECT {i}")

        jobs = list_jobs(db_path)
        assert len(jobs) == 5


class TestClaimNextJob:
    def test_claims_oldest_queued_job(self, db_path):
        id1 = generate_job_id()
        id2 = generate_job_id()
        insert_job(db_path, id1, "SELECT 1")
        time.sleep(0.01)  # Ensure different timestamps
        insert_job(db_path, id2, "SELECT 2")

        claimed = claim_next_job(db_path)
        assert claimed is not None
        assert claimed["job_id"] == id1
        assert claimed["status"] == "running"
        assert claimed["started_at"] is not None

    def test_does_not_claim_running_job(self, db_path):
        id1 = generate_job_id()
        insert_job(db_path, id1, "SELECT 1")

        # Claim the first one
        claim_next_job(db_path)

        # No more queued jobs
        claimed = claim_next_job(db_path)
        assert claimed is None

    def test_returns_none_when_queue_empty(self, db_path):
        claimed = claim_next_job(db_path)
        assert claimed is None


class TestUpdateJobStatus:
    def test_transition_to_succeeded(self, db_path):
        job_id = generate_job_id()
        insert_job(db_path, job_id, "SELECT 1")
        claim_next_job(db_path)

        job = update_job_status(db_path, job_id, "succeeded")
        assert job["status"] == "succeeded"
        assert job["completed_at"] is not None
        assert job["error_message"] is None

    def test_transition_to_failed_with_error(self, db_path):
        job_id = generate_job_id()
        insert_job(db_path, job_id, "INVALID SQL")
        claim_next_job(db_path)

        job = update_job_status(db_path, job_id, "failed", error_message="Syntax error")
        assert job["status"] == "failed"
        assert job["error_message"] == "Syntax error"
        assert job["completed_at"] is not None


class TestGetJob:
    def test_get_existing_job(self, db_path):
        job_id = generate_job_id()
        insert_job(db_path, job_id, "SELECT 1")

        job = get_job(db_path, job_id)
        assert job is not None
        assert job["job_id"] == job_id

    def test_get_nonexistent_job(self, db_path):
        job = get_job(db_path, "nonexistent")
        assert job is None


class TestListJobs:
    def test_lists_jobs_newest_first(self, db_path):
        ids = []
        for i in range(3):
            jid = generate_job_id()
            ids.append(jid)
            insert_job(db_path, jid, f"SELECT {i}")
            time.sleep(0.01)

        jobs = list_jobs(db_path)
        assert len(jobs) == 3
        # Newest first
        assert jobs[0]["job_id"] == ids[2]
        assert jobs[2]["job_id"] == ids[0]


class TestCleanupOldJobs:
    def test_removes_excess_jobs(self, db_path):
        ids = []
        for i in range(5):
            jid = generate_job_id()
            ids.append(jid)
            insert_job(db_path, jid, f"SELECT {i}")
            time.sleep(0.01)

        # Keep only 3
        deleted = cleanup_old_jobs(db_path, max_jobs=3)
        assert len(deleted) == 2
        # Oldest two should be deleted
        assert ids[0] in deleted
        assert ids[1] in deleted

        remaining = list_jobs(db_path)
        assert len(remaining) == 3

    def test_no_cleanup_needed(self, db_path):
        for i in range(3):
            insert_job(db_path, generate_job_id(), f"SELECT {i}")

        deleted = cleanup_old_jobs(db_path, max_jobs=10)
        assert len(deleted) == 0
        assert len(list_jobs(db_path)) == 3
