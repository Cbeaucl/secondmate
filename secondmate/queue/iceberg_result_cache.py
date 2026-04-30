import re
import logging

from pyspark.sql import SparkSession, DataFrame

from secondmate.utils import sanitize_for_serialization
from secondmate.queue.result_cache import ResultCache

logger = logging.getLogger(__name__)


def _sanitize_table_name(job_id: str) -> str:
    """Sanitize a job_id into a valid table name component."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", job_id)


class IcebergResultCache(ResultCache):
    """Stores query results as Iceberg tables.

    Default location: users.secondmate.job_<job_id>
    """

    def __init__(self, catalog: str, namespace: str):
        self.catalog = catalog
        self.namespace = namespace

    def initialize(self, spark: SparkSession) -> None:
        """Check if the target catalog and namespace exist."""
        fqn = f"{self.catalog}.{self.namespace}"
        try:
            res = spark.sql(f"SHOW NAMESPACES IN {self.catalog} LIKE '{self.namespace}'").collect()
            if len(res) == 0:
                logger.warning(f"Result namespace {fqn} does not exist.")
                raise RuntimeError(f"Namespace {fqn} does not exist.")
            logger.info(f"Verified namespace {fqn} exists")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            logger.warning(f"Result catalog or namespace {fqn} could not be found or verified.", exc_info=True)
            raise RuntimeError(f"Catalog or namespace {fqn} does not exist or is invalid.") from e

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
            spark.sql(f"DROP TABLE IF EXISTS {table} PURGE")
        except Exception:
            logger.warning(f"Failed to drop result table {table}", exc_info=True)
