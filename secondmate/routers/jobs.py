"""
API router for the job queue system.

Provides endpoints to submit jobs, list jobs, get job details,
and fetch results for completed jobs.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from secondmate.queue import db as queue_db
from secondmate.queue.result_cache import ResultCache
from secondmate.queue.iceberg_result_cache import IcebergResultCache
from secondmate.dependencies import get_spark_provider
from secondmate.utils import sanitize_for_serialization

logger = logging.getLogger(__name__)

router = APIRouter()

# These will be set during app startup via configure()
_db_path: str = ""
_result_cache: ResultCache | None = None


def configure(db_path: str, result_cache: ResultCache):
    """Called at startup to inject the DB path and result cache instance."""
    global _db_path, _result_cache
    _db_path = db_path
    _result_cache = result_cache


class SubmitRequest(BaseModel):
    query: str


@router.post("/jobs/submit")
def submit_job(request: SubmitRequest):
    """Submit a new query to the job queue.

    Returns the generated job_id so the client can poll for status.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    job_id = queue_db.generate_job_id()
    job = queue_db.insert_job(_db_path, job_id, request.query)
    return {"job_id": job["job_id"], "status": job["status"]}


@router.get("/jobs")
def list_jobs():
    """List all jobs, ordered by creation time (newest first)."""
    jobs = queue_db.list_jobs(_db_path)
    return {"jobs": jobs}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Get the details of a specific job."""
    job = queue_db.get_job(_db_path, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/results")
def get_job_results(job_id: str, provider=Depends(get_spark_provider)):
    """Fetch the results for a completed job from the result cache.

    Only available for jobs with status 'succeeded'.
    """
    job = queue_db.get_job(_db_path, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "succeeded":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not complete (status: {job['status']})"
        )

    try:
        spark = provider.get_session()
        schema, data = _result_cache.load(job_id, spark)
        return {"schema": schema, "data": data}
    except Exception as e:
        logger.error(f"Failed to load results for job {job_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load results: {str(e)}")
