from fastapi import FastAPI, Depends, APIRouter, HTTPException
from pyspark.sql import SparkSession
from secondmate.dependencies import get_spark_session
import sys
import os
import logging
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Hack to make sure pyspark finds the right python executable if needed, 
# or relying on environment. 
# For local spark, PYSPARK_PYTHON usually defaults to sys.executable

from contextlib import asynccontextmanager
from secondmate.dependencies import get_spark_provider

from secondmate.providers.local_spark import LocalSparkProvider
from secondmate.dev_data import initialize_dev_data
from secondmate.models import ConfigOption
from typing import Dict, Any, List
import re
import base64

def sanitize_for_serialization(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize_for_serialization(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_serialization(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_for_serialization(v) for v in obj)
    elif isinstance(obj, (bytes, bytearray)):
        try:
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            return base64.b64encode(obj).decode('utf-8')
    return obj

def validate_identifier(name: str):
    """Validate that an identifier only contains alphanumeric characters, underscores, and dots."""
    if not re.match(r"^[a-zA-Z0-9_.]+\Z", name):
        raise HTTPException(status_code=400, detail=f"Invalid identifier: {name}")

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure table exists and has data
    provider = get_spark_provider()
    spark = provider.get_session()
    
    # Only create fake data if using LocalSparkProvider
    if isinstance(provider, LocalSparkProvider):
        initialize_dev_data(spark)

    yield
    # Shutdown logic if needed

app = FastAPI(title="SecondMate Backend", lifespan=lifespan)
router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/query/execute")
def execute_query(request: QueryRequest, provider = Depends(get_spark_provider)):
    """Execute a raw SQL query and return results."""
    # Validate required configs
    configs = provider.get_configs()
    for config in configs:
        if config.is_required and (config.current_value is None or config.current_value == ""):
            raise HTTPException(status_code=400, detail=f"Required configuration '{config.label}' is missing.")

    try:
        spark = provider.get_session()
        df = spark.sql(request.query)
        # Limit to 1000 to prevent overloading
        df = df.limit(1000)
        
        # Get schema
        schema = [{"name": field.name, "type": str(field.dataType)} for field in df.schema.fields]
        
        # Get data
        data = [row.asDict(recursive=True) for row in df.collect()]
        data = sanitize_for_serialization(data)
        
        return {"schema": schema, "data": data}
    except Exception:
        logger.error("Error executing query", exc_info=True)
        return {"error": "An error occurred while executing the query."}

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
    except Exception:
        logger.error("Error retrieving catalogs", exc_info=True)
        return {"catalogs": [], "error": "Unable to retrieve catalogs."}

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
    except Exception:
        logger.error(f"Error retrieving namespaces for catalog {catalog_name}", exc_info=True)
        return {"namespaces": [], "error": "Unable to retrieve namespaces."}

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
    except Exception:
        logger.error(f"Error retrieving tables for {catalog_name}.{namespace}", exc_info=True)
        return {"tables": [], "error": "Unable to retrieve tables."}

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/overview")
def get_table_overview(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    """Get an overview of an Iceberg table including schema, properties, snapshots, partitions, and files."""
    validate_identifier(catalog_name)
    validate_identifier(namespace)
    validate_identifier(table_name)

    full_table_name = f"{catalog_name}.{namespace}.{table_name}"

    try:
        # 1. Schema
        df = spark.table(full_table_name)
        schema_json = df.schema.jsonValue()

        # Helper to get data from metadata tables or return empty list if not supported
        def get_metadata(suffix, query=None):
            try:
                if query:
                    m_df = spark.sql(query)
                else:
                    m_df = spark.sql(f"SELECT * FROM {full_table_name}.{suffix}")
                rows = [row.asDict(recursive=True) for row in m_df.collect()]
                return sanitize_for_serialization(rows)
            except Exception as e:
                logger.warning(f"Metadata table {suffix} not available for {full_table_name}: {e}")
                return []

        # 2. Properties
        properties = get_metadata("properties", f"SHOW TBLPROPERTIES {full_table_name}")

        # 3. Snapshots (ordered by latest, limit 250)
        snapshots = get_metadata("snapshots", f"SELECT * FROM {full_table_name}.snapshots ORDER BY committed_at DESC LIMIT 250")

        # 4. Partitions (limit 250)
        partitions = get_metadata("partitions", f"SELECT * FROM {full_table_name}.partitions LIMIT 250")

        # 5. Files (exclude file_path, convert size to MB, limit 250)
        partition_col = ""
        try:
            if "partition" in spark.table(f"{full_table_name}.files").columns:
                partition_col = "partition,"
        except Exception:
            pass

        files = get_metadata("files", f"""
            SELECT
                content,
                file_format,
                spec_id,
                {partition_col}
                record_count,
                file_size_in_bytes / (1024.0 * 1024.0) as file_size_mb,
                column_sizes,
                value_counts,
                null_value_counts,
                nan_value_counts,
                lower_bounds,
                upper_bounds,
                key_metadata,
                split_offsets,
                equality_ids,
                sort_order_id
            FROM {full_table_name}.files
            LIMIT 250
        """)

        return {
            "tableName": full_table_name,
            "schema": schema_json,
            "properties": properties,
            "snapshots": snapshots,
            "partitions": partitions,
            "files": files
        }
    except Exception:
        logger.error(f"Error retrieving overview for {full_table_name}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unable to retrieve overview for table {full_table_name}")

@router.get("/configs", response_model=List[ConfigOption])
def get_configs(provider=Depends(get_spark_provider)):
    """Get the current configurations."""
    return provider.get_configs()

@router.post("/configs")
def set_configs(configs: Dict[str, Any], provider=Depends(get_spark_provider)):
    """Update the configurations."""
    try:
        provider.set_configs(configs)
        return {"status": "ok"}
    except Exception as e:
        logger.error("Error updating configurations", exc_info=True)
        raise HTTPException(status_code=422, detail=str(e))

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

    except Exception:
        logger.error("Error during catalog search", exc_info=True)
        return {"results": [], "error": "An error occurred during search."}

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
