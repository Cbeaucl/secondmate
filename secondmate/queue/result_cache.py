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


def _sanitize_table_name(job_id: str) -> str:
    """Sanitize a job_id into a valid table name component."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", job_id)


class IcebergResultCache:
    """Stores query results as Iceberg tables.

    Default location: users.secondmate.job_<job_id>
    """

    def __init__(self, catalog: str = "user", namespace: str = "secondmate"):
        self.catalog = catalog
        self.namespace = namespace

    def initialize(self, spark: SparkSession) -> None:
        """Create the target namespace if it doesn't exist."""
        fqn = f"{self.catalog}.{self.namespace}"
        try:
            spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {fqn}")
            logger.info(f"Ensured namespace {fqn} exists")
        except Exception:
            logger.warning(f"Could not create namespace {fqn}", exc_info=True)

    def _table_name(self, job_id: str) -> str:
        safe_id = _sanitize_table_name(job_id)
        return f"{self.catalog}.{self.namespace}.job_{safe_id}"

    def save(self, job_id: str, df: DataFrame) -> None:
        """Write the DataFrame as an Iceberg table."""
        table = self._table_name(job_id)
        logger.info(f"Saving results to {table}")
        # Limit results to prevent massive result sets
        limited_df = df.limit(1000)
        limited_df.writeTo(table).createOrReplace()

    def load(self, job_id: str, spark: SparkSession) -> tuple[list[dict], list[dict]]:
        """Read results from the Iceberg table.

        Returns (schema, data) matching the format of the old /query/execute endpoint.
        """
        table = self._table_name(job_id)
        logger.info(f"Loading results from {table}")
        df = spark.table(table)

        schema = [
            {"name": field.name, "type": str(field.dataType)}
            for field in df.schema.fields
        ]
        data = [row.asDict(recursive=True) for row in df.collect()]
        data = sanitize_for_serialization(data)

        return schema, data

    def delete(self, job_id: str, spark: SparkSession) -> None:
        """Drop the Iceberg result table."""
        table = self._table_name(job_id)
        logger.info(f"Deleting result table {table}")
        try:
            spark.sql(f"DROP TABLE IF EXISTS {table}")
        except Exception:
            logger.warning(f"Failed to drop result table {table}", exc_info=True)
