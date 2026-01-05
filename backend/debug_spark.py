from pyspark.sql import SparkSession
import os
import sys

def test_spark():
    print("Testing Spark Session creation with Iceberg...")
    print(f"Python: {sys.version}")
    
    try:
        spark = (
            SparkSession.builder
            .appName("SecondMateDebug")
            .master("local[*]")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.driver.host", "127.0.0.1")
            .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-4.0_2.13:1.10.0")
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
            .config("spark.sql.catalog.user", "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.user.type", "hadoop")
            .config("spark.sql.catalog.user.warehouse", "warehouse")
            .getOrCreate()
        )
        print("Spark Session created successfully.")
        print(f"Spark Version: {spark.version}")
        
        print("Creating table...")
        spark.sql("CREATE TABLE IF NOT EXISTS user.ipgeo (id LONG, ip STRING, city STRING, country STRING) USING iceberg")
        print("Table created/verified.")
        
        print("Inserting data...")
        data = [(1, "1.1.1.1", "TestCity", "TestCountry")]
        df = spark.createDataFrame(data, ["id", "ip", "city", "country"])
        df.writeTo("user.ipgeo").append()
        print("Data inserted.")
        
        print("Reading data...")
        df_read = spark.sql("SELECT * FROM user.ipgeo")
        df_read.show()
        print("Read successful.")
        
        spark.stop()
        print("Spark stopped.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spark()
