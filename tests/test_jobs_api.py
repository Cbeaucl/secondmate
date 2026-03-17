"""Tests for the jobs API router endpoints."""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from secondmate.routers.jobs import router, configure
from secondmate.queue.db import init_db, generate_job_id, insert_job, claim_next_job, update_job_status


@pytest.fixture
def db_path():
    """Create a temporary database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    init_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def mock_result_cache():
    cache = MagicMock()
    cache.load.return_value = (
        [{"name": "id", "type": "IntegerType"}],
        [{"id": 1}, {"id": 2}],
    )
    return cache


@pytest.fixture
def client(db_path, mock_result_cache):
    """Create a test client with the jobs router."""
    app = FastAPI()

    # Mock the spark provider dependency
    mock_provider = MagicMock()
    app.dependency_overrides = {}

    from secondmate.dependencies import get_spark_provider
    app.dependency_overrides[get_spark_provider] = lambda: mock_provider

    app.include_router(router, prefix="/api")
    configure(db_path, mock_result_cache)
    return TestClient(app)


class TestSubmitJob:
    def test_submit_returns_job_id(self, client):
        response = client.post("/api/jobs/submit", json={"query": "SELECT 1"})
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_submit_empty_query_returns_400(self, client):
        response = client.post("/api/jobs/submit", json={"query": "  "})
        assert response.status_code == 400


class TestListJobs:
    def test_list_returns_jobs(self, client, db_path):
        # Insert some jobs directly
        insert_job(db_path, generate_job_id(), "SELECT 1")
        insert_job(db_path, generate_job_id(), "SELECT 2")

        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) >= 2

    def test_list_empty(self, client):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert response.json()["jobs"] == []


class TestGetJob:
    def test_get_existing_job(self, client, db_path):
        job_id = generate_job_id()
        insert_job(db_path, job_id, "SELECT 1")

        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["job_id"] == job_id

    def test_get_nonexistent_job(self, client):
        response = client.get("/api/jobs/nonexistent")
        assert response.status_code == 404


class TestGetJobResults:
    def test_results_for_succeeded_job(self, client, db_path, mock_result_cache):
        job_id = generate_job_id()
        insert_job(db_path, job_id, "SELECT 1")
        claim_next_job(db_path)
        update_job_status(db_path, job_id, "succeeded")

        response = client.get(f"/api/jobs/{job_id}/results")
        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert "data" in data
        assert len(data["data"]) == 2

    def test_results_for_non_succeeded_job(self, client, db_path):
        job_id = generate_job_id()
        insert_job(db_path, job_id, "SELECT 1")

        response = client.get(f"/api/jobs/{job_id}/results")
        assert response.status_code == 400

    def test_results_for_nonexistent_job(self, client):
        response = client.get("/api/jobs/nonexistent/results")
        assert response.status_code == 404
