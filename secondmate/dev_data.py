import logging
from pyspark.sql import SparkSession
from datetime import date

logger = logging.getLogger(__name__)

def create_table_if_not_exists(spark: SparkSession, table_name: str, schema_ddl: str, data_records: list, partition_by: str = None):
    if not spark.catalog.tableExists(table_name):
        print(f"Creating {table_name} table...")
        ddl = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema_ddl}) USING iceberg"
        if partition_by:
            ddl += f" PARTITIONED BY ({partition_by})"
        spark.sql(ddl)
    
    # Check if empty
    count = spark.table(table_name).count()
    if count == 0 and data_records:
        print(f"Populating {table_name} with {len(data_records)} rows...")
        df = spark.createDataFrame(data_records, schema_ddl)
        df.writeTo(table_name).append()
        print(f"Initialized {table_name} with {len(data_records)} rows.")
    else:
         print(f"Table {table_name} already has {count} rows.")

def initialize_dev_data(spark: SparkSession):
    # 1. user.ipgeo
    create_table_if_not_exists(
        spark,
        "user.ipgeo", 
        "id LONG, ip STRING, city STRING, country STRING", 
        [(i, f"192.168.1.{i % 255}", f"City_{i}", f"Country_{i % 10}") for i in range(1000)]
    )

    # 2. user.sales.transactions
    spark.sql("CREATE NAMESPACE IF NOT EXISTS user.sales")
    create_table_if_not_exists(
        spark,
        "user.sales.transactions",
        "tx_id LONG, amount DOUBLE, currency STRING, tx_date DATE",
        [
            (1, 100.50, "USD", date(2023, 1, 1)),
            (2, 200.00, "EUR", date(2023, 1, 2)),
            (3, 50.25, "GBP", date(2023, 1, 3))
        ]
    )

    # 3. user.finance.budget
    spark.sql("CREATE NAMESPACE IF NOT EXISTS user.finance")
    create_table_if_not_exists(
        spark,
        "user.finance.budget",
        "dept_id LONG, dept_name STRING, budget_amount DOUBLE, fiscal_year INT",
        [
            (101, "Engineering", 500000.0, 2024),
            (102, "Marketing", 200000.0, 2024),
            (103, "HR", 150000.0, 2024)
        ]
    )

    # 4. user.activity.logs (complex & partitioned)
    spark.sql("CREATE NAMESPACE IF NOT EXISTS user.activity")
    create_table_if_not_exists(
        spark,
        "user.activity.logs",
        "log_id LONG, event STRUCT<name: STRING, context: STRUCT<ip: STRING, browser: STRING>>, log_date DATE",
        [
            (1, {"name": "login", "context": {"ip": "192.168.1.1", "browser": "Chrome"}}, date(2023, 10, 1)),
            (2, {"name": "click", "context": {"ip": "192.168.1.2", "browser": "Firefox"}}, date(2023, 10, 1)),
            (3, {"name": "logout", "context": {"ip": "192.168.1.1", "browser": "Chrome"}}, date(2023, 10, 2)),
            (4, {"name": "login", "context": {"ip": "10.0.0.1", "browser": "Safari"}}, date(2023, 10, 2)),
        ],
        partition_by="log_date"
    )
