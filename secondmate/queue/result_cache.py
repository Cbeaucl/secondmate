"""
Pluggable result cache for storing query job outputs.

The default IcebergResultCache writes results to Iceberg tables.
Other implementations (in-memory, JSON file, etc.) can be created
by implementing the ResultCache protocol.
"""
import re
import logging
from typing import Protocol, runtime_checkable

from pyspark.sql import SparkSession, DataFrame

from secondmate.utils import sanitize_for_serialization

logger = logging.getLogger(__name__)


@runtime_checkable
class ResultCache(Protocol):
    """Protocol for result cache implementations."""

    def initialize(self, spark: SparkSession) -> None:
        """Perform any one-time setup (e.g., creating namespaces). Called at startup."""
        ...

    def save(self, job_id: str, df: DataFrame) -> None:
        """Persist the DataFrame result for a given job."""
        ...

    def load(self, job_id: str, spark: SparkSession) -> tuple[list[dict], list[dict]]:
        """Load results for a job. Returns (schema, data)."""
        ...

    def delete(self, job_id: str, spark: SparkSession) -> None:
        """Delete stored results for a job."""
        ...


