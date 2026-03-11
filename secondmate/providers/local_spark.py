from typing import List, Dict, Any
from pyspark.sql import SparkSession
from secondmate.providers.spark_interface import SparkProvider
from secondmate.models import ConfigOption, DataType, UiInputType, ConfigOptionItem

class LocalSparkProvider(SparkProvider):
    def __init__(self, app_name: str = "SecondMateLocal"):
        self.app_name = app_name
        self._session = None
        self._configs = {
            "spark.executor.memory": ConfigOption(
                id="spark.executor.memory",
                label="Executor Memory",
                data_type=DataType.STRING,
                ui_input_type=UiInputType.TEXT,
                current_value="1g",
                default_value="1g",
                is_required=True
            ),
            "spark.driver.memory": ConfigOption(
                id="spark.driver.memory",
                label="Driver Memory",
                data_type=DataType.STRING,
                ui_input_type=UiInputType.TEXT,
                current_value="1g",
                default_value="1g",
                is_required=True
            ),
            "spark.sql.shuffle.partitions": ConfigOption(
                id="spark.sql.shuffle.partitions",
                label="Shuffle Partitions",
                data_type=DataType.INTEGER,
                ui_input_type=UiInputType.TEXT,
                current_value=200,
                default_value=200,
                is_required=False
            )
        }

    def get_session(self) -> SparkSession:
        if self._session is None:
            builder = (
                SparkSession.builder
                .appName(self.app_name)
                .master("local[*]")
                .config("spark.driver.bindAddress", "127.0.0.1")
                .config("spark.driver.host", "127.0.0.1")
                # Iceberg Configuration
                .config("spark.jars.packages", "org.xerial:sqlite-jdbc:3.45.1.0,org.apache.iceberg:iceberg-spark-runtime-4.0_2.13:1.10.0")
                .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
                .config("spark.sql.catalog.user", "org.apache.iceberg.spark.SparkCatalog")
                .config("spark.sql.catalog.user.type", "jdbc")
                .config("spark.sql.catalog.user.uri", "jdbc:sqlite:iceberg_catalog.db")
                .config("spark.sql.catalog.user.jdbc.user", "user")
                .config("spark.sql.catalog.user.jdbc.password", "password")
                .config("spark.sql.catalog.user.jdbc.schema-version", "V1")
                .config("spark.sql.catalog.user.warehouse", "warehouse")
            )

            # Apply dynamic configs
            for config_id, config_opt in self._configs.items():
                if config_opt.current_value is not None:
                    builder = builder.config(config_id, config_opt.current_value)

            self._session = builder.getOrCreate()
        return self._session

    def get_configs(self) -> List[ConfigOption]:
        return list(self._configs.values())

    def set_configs(self, configs: Dict[str, Any]) -> None:
        restart_needed = False
        for config_id, value in configs.items():
            if config_id in self._configs:
                if self._configs[config_id].current_value != value:
                    self._configs[config_id].current_value = value
                    # In a real Spark environment, most configs require restart if session exists
                    restart_needed = True

        if restart_needed and self._session is not None:
            self._session.stop()
            self._session = None
