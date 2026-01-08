from pyspark.sql import SparkSession
from secondmate.providers.spark_interface import SparkProvider

class LocalSparkProvider(SparkProvider):
    def __init__(self, app_name: str = "SecondMateLocal"):
        self.app_name = app_name
        self._session = None

    def get_session(self) -> SparkSession:
        if self._session is None:
            self._session = (
                SparkSession.builder
                .appName(self.app_name)
                .master("local[*]")
                .config("spark.driver.bindAddress", "127.0.0.1")
                .config("spark.driver.host", "127.0.0.1")
                # Iceberg Configuration
                .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-4.0_2.13:1.10.0")
                .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
                .config("spark.sql.catalog.user", "org.apache.iceberg.spark.SparkCatalog")
                .config("spark.sql.catalog.user.type", "hadoop")
                .config("spark.sql.catalog.user.warehouse", "warehouse")
                .getOrCreate()
            )
        return self._session
