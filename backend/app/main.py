from fastapi import FastAPI, Depends
from pyspark.sql import SparkSession
from app.dependencies import get_spark_session
import sys

# Hack to make sure pyspark finds the right python executable if needed, 
# or relying on environment. 
# For local spark, PYSPARK_PYTHON usually defaults to sys.executable

from contextlib import asynccontextmanager
from app.dependencies import get_spark_provider
import random

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure table exists and has data
    spark = get_spark_provider().get_session()
    
    # helper to create table with data
    def create_table_if_not_exists(table_name, schema_ddl, data_records, schema_cols):
        if not spark.catalog.tableExists(table_name):
            print(f"Creating {table_name} table...")
            spark.sql(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema_ddl}) USING iceberg")
        
        # Check if empty
        count = spark.table(table_name).count()
        if count == 0 and data_records:
            print(f"Populating {table_name} with {len(data_records)} rows...")
            df = spark.createDataFrame(data_records, schema_cols)
            df.writeTo(table_name).append()
            print(f"Initialized {table_name} with {len(data_records)} rows.")
        else:
             print(f"Table {table_name} already has {count} rows.")

    # 1. user.ipgeo
    create_table_if_not_exists(
        "user.ipgeo", 
        "id LONG, ip STRING, city STRING, country STRING", 
        [(i, f"192.168.1.{i % 255}", f"City_{i}", f"Country_{i % 10}") for i in range(1000)],
        ["id", "ip", "city", "country"]
    )

    # 2. user.sales.transactions
    from datetime import date
    spark.sql("CREATE NAMESPACE IF NOT EXISTS user.sales")
    create_table_if_not_exists(
        "user.sales.transactions",
        "tx_id LONG, amount DOUBLE, currency STRING, tx_date DATE",
        [
            (1, 100.50, "USD", date(2023, 1, 1)),
            (2, 200.00, "EUR", date(2023, 1, 2)),
            (3, 50.25, "GBP", date(2023, 1, 3))
        ],
        ["tx_id", "amount", "currency", "tx_date"]
    )

    # 3. user.finance.budget
    spark.sql("CREATE NAMESPACE IF NOT EXISTS user.finance")
    create_table_if_not_exists(
        "user.finance.budget",
        "dept_id LONG, dept_name STRING, budget_amount DOUBLE, fiscal_year INT",
        [
            (101, "Engineering", 500000.0, 2024),
            (102, "Marketing", 200000.0, 2024),
            (103, "HR", 150000.0, 2024)
        ],
        ["dept_id", "dept_name", "budget_amount", "fiscal_year"]
    )

    yield
    # Shutdown logic if needed

app = FastAPI(title="SecondMate Backend", lifespan=lifespan)

from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

@app.post("/query/execute")
def execute_query(request: QueryRequest, spark: SparkSession = Depends(get_spark_session)):
    """Execute a raw SQL query and return results."""
    try:
        df = spark.sql(request.query)
        # Limit to 1000 to prevent overloading
        df = df.limit(1000)
        
        # Get schema
        schema = [{"name": field.name, "type": str(field.dataType)} for field in df.schema.fields]
        
        # Get data
        data = [row.asDict() for row in df.collect()]
        
        return {"schema": schema, "data": data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/catalogs")
def get_catalogs(spark: SparkSession = Depends(get_spark_session)):
    """List available catalogs."""
    # In PySpark 3.4+, spark.catalog.listCatalogs() exists but might not be standard in all setups.
    # For now, we can try to inspect catalogs.
    # A standard Spark setup usually has 'spark_catalog' and any defined custom catalogs.
    # We can try to query `SHOW CATALOGS` via SQL
    try:
        df = spark.sql("SHOW CATALOGS")
        catalogs = [row.catalog for row in df.collect()]
        return {"catalogs": catalogs}
    except Exception as e:
        return {"catalogs": [], "error": str(e)}

@app.get("/catalogs/{catalog_name}/namespaces")
def get_namespaces(catalog_name: str, spark: SparkSession = Depends(get_spark_session)):
    """List namespaces in a specific catalog."""
    try:
        # Switch to catalog to list namespaces easily, or use `SHOW NAMESPACES IN catalog`
        df = spark.sql(f"SHOW NAMESPACES IN {catalog_name}")
        # The column name is usually 'namespace'
        namespaces = [row.namespace for row in df.collect()]
        return {"namespaces": namespaces}
    except Exception as e:
        return {"namespaces": [], "error": str(e)}

@app.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables")
def get_tables(catalog_name: str, namespace: str, spark: SparkSession = Depends(get_spark_session)):
    """List tables in a specific namespace."""
    try:
        df = spark.sql(f"SHOW TABLES IN {catalog_name}.{namespace}")
        # Columns: 'namespace', 'tableName', 'isTemporary'
        tables = [row.tableName for row in df.collect()]
        return {"tables": tables}
    except Exception as e:
        return {"tables": [], "error": str(e)}

@app.get("/info")
def get_info(spark: SparkSession = Depends(get_spark_session)):
    return {
        "app_name": spark.sparkContext.appName,
        "spark_version": spark.version,
        "master": spark.sparkContext.master,
        "python_version": sys.version
    }



@app.get("/health")
def health_check():
    return {"status": "ok"}
