from fastapi import FastAPI, Depends, APIRouter, HTTPException
from pyspark.sql import SparkSession
from secondmate.dependencies import get_spark_session
import sys
import os
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Hack to make sure pyspark finds the right python executable if needed, 
# or relying on environment. 
# For local spark, PYSPARK_PYTHON usually defaults to sys.executable

from contextlib import asynccontextmanager
from secondmate.dependencies import get_spark_provider

from secondmate.providers.local_spark import LocalSparkProvider
import re

def validate_identifier(name: str):
    """Validate that an identifier only contains alphanumeric characters, underscores, and dots."""
    if not re.match(r"^[a-zA-Z0-9_.]+\Z", name):
        raise HTTPException(status_code=400, detail=f"Invalid identifier: {name}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure table exists and has data
    provider = get_spark_provider()
    spark = provider.get_session()
    
    # Only create fake data if using LocalSparkProvider
    if isinstance(provider, LocalSparkProvider):
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
router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/query/execute")
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

@router.get("/catalogs")
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

@router.get("/catalogs/{catalog_name}/namespaces")
def get_namespaces(catalog_name: str, spark: SparkSession = Depends(get_spark_session)):
    """List namespaces in a specific catalog."""
    validate_identifier(catalog_name)
    try:
        # Switch to catalog to list namespaces easily, or use `SHOW NAMESPACES IN catalog`
        df = spark.sql(f"SHOW NAMESPACES IN {catalog_name}")
        # The column name is usually 'namespace'
        namespaces = [row.namespace for row in df.collect()]
        return {"namespaces": namespaces}
    except Exception as e:
        return {"namespaces": [], "error": str(e)}

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables")
def get_tables(catalog_name: str, namespace: str, spark: SparkSession = Depends(get_spark_session)):
    """List tables in a specific namespace."""
    validate_identifier(catalog_name)
    validate_identifier(namespace)
    try:
        df = spark.sql(f"SHOW TABLES IN {catalog_name}.{namespace}")
        # Columns: 'namespace', 'tableName', 'isTemporary'
        tables = [row.tableName for row in df.collect()]
        return {"tables": tables}
    except Exception as e:
        return {"tables": [], "error": str(e)}

@router.get("/info")
def get_info(spark: SparkSession = Depends(get_spark_session)):
    return {
        "app_name": spark.sparkContext.appName,
        "spark_version": spark.version,
        "master": spark.sparkContext.master,
        "python_version": sys.version
    }



@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/search")
def search_catalog(q: str, spark: SparkSession = Depends(get_spark_session)):
    """Search for catalogs, namespaces, and tables matching the query."""
    query = q.lower()
    results = []

    try:
        # 1. Search Catalogs
        df_catalogs = spark.sql("SHOW CATALOGS")
        catalogs = [row.catalog for row in df_catalogs.collect()]
        
        for cat in catalogs:
            if query in cat.lower():
                results.append({"type": "catalog", "catalog": cat, "name": cat})
            
            try:
                # 2. Search Namespaces within Catalog
                df_ns = spark.sql(f"SHOW NAMESPACES IN {cat}")
                namespaces = [row.namespace for row in df_ns.collect()]
                
                for ns in namespaces:
                    if query in ns.lower():
                        results.append({"type": "namespace", "catalog": cat, "namespace": ns, "name": ns})
                    
                    try:
                        # 3. Search Tables within Namespace
                        df_tables = spark.sql(f"SHOW TABLES IN {cat}.{ns}")
                        tables = [row.tableName for row in df_tables.collect()]
                        
                        for table in tables:
                            if query in table.lower():
                                results.append({
                                    "type": "table", 
                                    "catalog": cat, 
                                    "namespace": ns, 
                                    "table": table,
                                    "name": table
                                })
                    except Exception:
                        continue # Ignore individual failures
            except Exception:
                continue

    except Exception as e:
        return {"results": [], "error": str(e)}

    return {"results": results}

# Include the API router
app.include_router(router, prefix="/api")

# Mount static files
# Use environment variable or fallback to local assumption
static_dir = os.getenv("SECONDMATE_STATIC_DIR", os.path.join(os.path.dirname(__file__), "static"))

if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Exclude API routes from catch-all
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
             from fastapi import HTTPException
             raise HTTPException(status_code=404, detail="Not Found")
        
        # Check if it's a static file that exists
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Fallback to index.html for SPA routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Determine base path for API
            # Priority: PROXY_PREFIX env var -> JUPYTERHUB_SERVICE_PREFIX -> default
            # Note: JUPYTERHUB_SERVICE_PREFIX is usually /user/<name>/
            # If running via jupyter-server-proxy, the URL is typically /user/<name>/proxy/<port>/
            # The user should ideally set PROXY_PREFIX to the full proxy path.
            proxy_prefix = os.getenv("PROXY_PREFIX", "")
            if not proxy_prefix and os.getenv("JUPYTERHUB_SERVICE_PREFIX"):
                 # Fallback/heuristic: if in jupyterhub, might still need port if using proxy
                 pass 

            # Ensure prefix has trailing slash if it exists and we're appending 'api'
            # But wait, if prefix is "/foo", we want "/foo/api"
            # If prefix is "/foo/", we want "/foo/api"
            api_base = "/api"
            if proxy_prefix:
                clean_prefix = proxy_prefix.rstrip("/")
                api_base = f"{clean_prefix}/api"

            injection = f'<script>window.SECONDMATE_CONFIG = {{ apiBaseUrl: "{api_base}" }};</script>'
            # Inject before </head>
            content = content.replace("</head>", f"{injection}</head>")
            
            return HTMLResponse(content=content)
        return {"error": "Frontend not built or static files missing."}
else:
    print(f"Warning: Static directory {static_dir} not found. Frontend will not be served.")
