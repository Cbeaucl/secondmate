from pyspark.sql import SparkSession
from secondmate.dev_data import initialize_dev_data
import json

spark = SparkSession.builder \
    .appName("ReproduceBug") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
    .config("spark.sql.catalog.spark_catalog.type", "hadoop") \
    .config("spark.sql.catalog.spark_catalog.warehouse", "/tmp/iceberg") \
    .getOrCreate()

initialize_dev_data(spark)

def get_metadata(full_table_name, suffix, query=None):
    try:
        if query:
            m_df = spark.sql(query)
        else:
            m_df = spark.sql(f"SELECT * FROM {full_table_name}.{suffix}")
        rows = [row.asDict(recursive=True) for row in m_df.collect()]
        return rows
    except Exception as e:
        print(f"Error fetching {suffix}: {e}")
        return []

full_table_name = "spark_catalog.user.ipgeo"
files = get_metadata(full_table_name, "files", f"""
    SELECT
        content,
        file_format,
        spec_id,
        partition,
        record_count,
        file_size_in_bytes / (1024.0 * 1024.0) as file_size_mb
    FROM {full_table_name}.files
    LIMIT 250
""")

print(f"Number of files for {full_table_name}: {len(files)}")
if len(files) > 0:
    print("First file partition info:", files[0]['partition'])

full_table_name_partitioned = "spark_catalog.user.activity.logs"
files_partitioned = get_metadata(full_table_name_partitioned, "files", f"""
    SELECT
        content,
        file_format,
        spec_id,
        partition,
        record_count,
        file_size_in_bytes / (1024.0 * 1024.0) as file_size_mb
    FROM {full_table_name_partitioned}.files
    LIMIT 250
""")

print(f"Number of files for {full_table_name_partitioned}: {len(files_partitioned)}")
if len(files_partitioned) > 0:
    print("First file partition info (partitioned):", files_partitioned[0]['partition'])

spark.stop()
