"""Tests for the background job runner with mocked Spark and result cache."""
import os
import time
import tempfile
import asyncio
import pytest
from unittest.mock import MagicMock, patch

from secondmate.queue.db import (
    init_db,
    generate_job_id,
    insert_job,
    get_job,
    list_jobs,
)
from secondmate.queue.runner import _execute_job, _run_cleanup


@pytest.fixture
def db_path():
    """Create a temporary database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    init_db(path)
    yield path
    os.unlink(path)


@pytest.fixture
def mock_spark_provider():
    """Create a mock Spark provider."""
    provider = MagicMock()
    mock_spark = MagicMock()
    provider.get_session.return_value = mock_spark
    provider.get_configs.return_value = []

    def get_provider():
        return provider

    return get_provider, provider, mock_spark


@pytest.fixture
def mock_result_cache():
    """Create a mock result cache."""
    cache = MagicMock()
    return cache


class TestExecuteJob:
    @pytest.mark.asyncio
    async def test_successful_execution(self, db_path, mock_spark_provider, mock_result_cache):
        get_provider, provider, mock_spark = mock_spark_provider

        job_id = generate_job_id()
        insert_job(db_path, job_id, "SELECT 1")

        # Simulate a claimed job
        job = {
            "job_id": job_id,
            "query_text": "SELECT 1",
            "status": "running",
        }

        mock_df = MagicMock()
        mock_spark.sql.return_value = mock_df

        await _execute_job(job, db_path, get_provider, mock_result_cache)

        # Verify the job is now succeeded
        updated = get_job(db_path, job_id)
        assert updated["status"] == "succeeded"

        # Verify Spark was called
        mock_spark.sql.assert_called_once_with("SELECT 1")

        # Verify result cache was called
        mock_result_cache.save.assert_called_once_with(job_id, mock_df)

    @pytest.mark.asyncio
    async def test_failed_execution(self, db_path, mock_spark_provider, mock_result_cache):
        get_provider, provider, mock_spark = mock_spark_provider

        job_id = generate_job_id()
        insert_job(db_path, job_id, "INVALID SQL")

        job = {
            "job_id": job_id,
            "query_text": "INVALID SQL",
            "status": "running",
        }

        # Make Spark throw an exception
        mock_spark.sql.side_effect = Exception("Parse error: INVALID SQL")

        await _execute_job(job, db_path, get_provider, mock_result_cache)

        # Verify the job is now failed with error message
        updated = get_job(db_path, job_id)
        assert updated["status"] == "failed"
        assert "Parse error" in updated["error_message"]

        # Result cache should NOT have been called
        mock_result_cache.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_required_config(self, db_path, mock_spark_provider, mock_result_cache):
        get_provider, provider, mock_spark = mock_spark_provider

        # Add a required config that's missing
        mock_config = MagicMock()
        mock_config.is_required = True
        mock_config.current_value = None
        mock_config.label = "Test Config"
        provider.get_configs.return_value = [mock_config]

        job_id = generate_job_id()
        insert_job(db_path, job_id, "SELECT 1")

        job = {
            "job_id": job_id,
            "query_text": "SELECT 1",
            "status": "running",
        }

        await _execute_job(job, db_path, get_provider, mock_result_cache)

        updated = get_job(db_path, job_id)
        assert updated["status"] == "failed"
        assert "Required configuration" in updated["error_message"]


class TestRunCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_deletes_result_tables(self, db_path, mock_spark_provider, mock_result_cache):
        get_provider, provider, mock_spark = mock_spark_provider

        # Insert more than max_jobs
        ids = []
        for i in range(5):
            jid = generate_job_id()
            ids.append(jid)
            insert_job(db_path, jid, f"SELECT {i}")
            time.sleep(0.01)

        # Patch MAX_JOBS to 3 for this test
        with patch("secondmate.queue.runner.MAX_JOBS", 3):
            await _run_cleanup(db_path, get_provider, mock_result_cache)

        # Verify oldest 2 were cleaned up
        remaining = list_jobs(db_path)
        assert len(remaining) == 3

        # Result cache delete should have been called for each evicted job
        assert mock_result_cache.delete.call_count == 2
