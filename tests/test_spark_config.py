import pytest
from fastapi.testclient import TestClient
from secondmate.main import app
from secondmate.dependencies import get_spark_provider
from secondmate.providers.local_spark import LocalSparkProvider

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

    # We should NOT call provider.get_session() here because it would try to start spark with invalid config
    # The validation happens in execute_query before get_spark_session dependency is even resolved?
    # Actually Depends(get_spark_session) might be resolved first.

    response = client.post("/api/query/execute", json={"query": "SELECT 1"})
    assert response.status_code == 400
    assert "Required configuration" in response.json()["detail"]

def test_execute_query_validation_success():
    # Set required configs to valid values
    client.post("/api/configs", json={"spark.executor.memory": "1g", "spark.driver.memory": "1g"})

    response = client.post("/api/query/execute", json={"query": "SELECT 1"})
    # It might fail because of spark session not being available in test env,
    # but it shouldn't be a 400 validation error.
    assert response.status_code != 400
