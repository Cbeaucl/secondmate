"""
Background job runner that polls the queue and executes queries.

Runs as an asyncio task within the FastAPI lifespan, processing
one job at a time from the SQLite queue.
"""
import asyncio
import logging
from typing import Optional

from secondmate.queue.db import (
    claim_next_job,
    update_job_status,
    cleanup_old_jobs,
)
from secondmate.queue.result_cache import ResultCache

logger = logging.getLogger(__name__)

# How often to poll for new jobs (seconds)
POLL_INTERVAL = 1.0

# Run cleanup every N iterations
CLEANUP_EVERY = 10

# Max jobs to keep in the queue
MAX_JOBS = 50


async def run_job_loop(
    db_path: str,
    get_spark_provider,
    result_cache: ResultCache,
):
    """Main runner loop. Call via asyncio.create_task in the app lifespan.

    Continuously polls for queued jobs, executes them, and stores results.
    """
    iteration = 0
    logger.info("Job runner started")

    while True:
        try:
            iteration += 1

            # Try to claim a job
            job = claim_next_job(db_path)

            if job:
                await _execute_job(job, db_path, get_spark_provider, result_cache)
            else:
                # No jobs to process, wait before polling again
                await asyncio.sleep(POLL_INTERVAL)

            # Periodic cleanup
            if iteration % CLEANUP_EVERY == 0:
                await _run_cleanup(db_path, get_spark_provider, result_cache)

        except asyncio.CancelledError:
            logger.info("Job runner cancelled, shutting down")
            break
        except Exception:
            logger.error("Unexpected error in job runner loop", exc_info=True)
            await asyncio.sleep(POLL_INTERVAL)


async def _execute_job(
    job: dict,
    db_path: str,
    get_spark_provider,
    result_cache: ResultCache,
):
    """Execute a single claimed job.

    Runs the query via Spark, saves results on success,
    captures errors on failure.
    """
    job_id = job["job_id"]
    query = job["query_text"]
    logger.info(f"Executing job {job_id}: {query[:100]}...")

    try:
        # Run the query in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _run_spark_query,
            query,
            job_id,
            get_spark_provider,
            result_cache,
        )

        update_job_status(db_path, job_id, "succeeded")
        logger.info(f"Job {job_id} succeeded")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Job {job_id} failed: {error_msg}")
        update_job_status(db_path, job_id, "failed", error_message=error_msg)


def _run_spark_query(
    query: str,
    job_id: str,
    get_spark_provider,
    result_cache: ResultCache,
):
    """Execute the Spark query and save results. Runs in a thread."""
    provider = get_spark_provider()
    spark = provider.get_session()

    # Validate required configs
    configs = provider.get_configs()
    for config in configs:
        if config.is_required and (config.current_value is None or config.current_value == ""):
            raise ValueError(f"Required configuration '{config.label}' is missing.")

    df = spark.sql(query)
    result_cache.save(job_id, df)


async def _run_cleanup(
    db_path: str,
    get_spark_provider,
    result_cache: ResultCache,
):
    """Clean up old jobs beyond the cap and delete their result tables."""
    try:
        deleted_ids = cleanup_old_jobs(db_path, MAX_JOBS)
        if deleted_ids:
            logger.info(f"Cleaning up {len(deleted_ids)} old jobs")
            provider = get_spark_provider()
            spark = provider.get_session()
            for job_id in deleted_ids:
                try:
                    result_cache.delete(job_id, spark)
                except Exception:
                    logger.warning(f"Failed to delete result cache for job {job_id}", exc_info=True)
    except Exception:
        logger.warning("Error during job cleanup", exc_info=True)
