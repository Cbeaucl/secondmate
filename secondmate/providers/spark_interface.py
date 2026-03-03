from typing import Protocol, List, Dict, Any
from pyspark.sql import SparkSession
from secondmate.models import ConfigOption

class SparkProvider(Protocol):
    def get_session(self) -> SparkSession:
        """Get or create a SparkSession."""
        ...

    def get_configs(self) -> List[ConfigOption]:
        """Return the current configurations."""
        ...

    def set_configs(self, configs: Dict[str, Any]) -> None:
        """Update the configurations."""
        ...
