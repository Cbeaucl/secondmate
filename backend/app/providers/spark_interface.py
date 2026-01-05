from typing import Protocol
from pyspark.sql import SparkSession

class SparkProvider(Protocol):
    def get_session(self) -> SparkSession:
        """Get or create a SparkSession."""
        ...
