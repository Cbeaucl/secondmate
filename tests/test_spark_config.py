import os
import tempfile
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from secondmate.main import app
from secondmate.dependencies import get_spark_provider
from secondmate.providers.local_spark import LocalSparkProvider
from secondmate.queue.db import init_db
from secondmate.queue.iceberg_result_cache import IcebergResultCache
from secondmate.routers.jobs import configure as configure_jobs


@pytest.fixture(autouse=True)
def setup_queue_db():
    """Ensure the queue DB is initialized before each test in this module."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_db(db_path)
    configure_jobs(db_path, IcebergResultCache("test_catalog", "test_namespace"))
    yield
    os.unlink(db_path)


client = TestClient(app)

def test_get_configs():
    response = client.get("/api/configs")
    assert response.status_code == 200
    configs = response.json()
    assert len(configs) > 0
    ids = [c["id"] for c in configs]
    assert "spark.executor.memory" in ids
    assert "spark.driver.memory" in ids

def test_set_configs():
    new_configs = {"spark.executor.memory": "2g"}
    response = client.post("/api/configs", json=new_configs)
    assert response.status_code == 200

    response = client.get("/api/configs")
    configs = response.json()
    exec_mem = next(c for c in configs if c["id"] == "spark.executor.memory")
    assert exec_mem["current_value"] == "2g"

def test_execute_query_validation_failure():
    # Set a required config to empty
    client.post("/api/configs", json={"spark.executor.memory": ""})

    # With the job queue, submission always succeeds — validation happens in the runner.
    # Here we verify the job can be submitted even with bad config.
    response = client.post("/api/jobs/submit", json={"query": "SELECT 1"})
    assert response.status_code == 200
    assert "job_id" in response.json()

def test_execute_query_validation_success():
    # Set required configs to valid values
    client.post("/api/configs", json={"spark.executor.memory": "1g", "spark.driver.memory": "1g"})

    response = client.post("/api/jobs/submit", json={"query": "SELECT 1"})
    assert response.status_code == 200
    assert "job_id" in response.json()
