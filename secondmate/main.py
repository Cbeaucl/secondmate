from fastapi import FastAPI, Depends, APIRouter, HTTPException
from pyspark.sql import SparkSession
from secondmate.dependencies import get_spark_session
import asyncio
import sys
import os
import logging
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from contextlib import asynccontextmanager
from secondmate.dependencies import get_spark_provider

from secondmate.providers.local_spark import LocalSparkProvider
from secondmate.dev_data import initialize_dev_data
from secondmate.models import ConfigOption
from typing import Dict, Any, List
from secondmate.utils import sanitize_for_serialization, validate_identifier
from secondmate.routers.table import router as table_router
from secondmate.routers.jobs import router as jobs_router, configure as configure_jobs
from secondmate.queue.db import init_db
from secondmate.queue.runner import run_job_loop
from secondmate.queue.result_cache import IcebergResultCache

logger = logging.getLogger(__name__)

# Path for the job queue SQLite database
QUEUE_DB_PATH = os.getenv("SECONDMATE_QUEUE_DB", "job_queue.db")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure table exists and has data
    provider = get_spark_provider()
    spark = provider.get_session()
    
    # Only create fake data if using LocalSparkProvider
    if isinstance(provider, LocalSparkProvider):
        initialize_dev_data(spark)

    # Initialize the job queue
    db_path = init_db(QUEUE_DB_PATH)
    result_cache = IcebergResultCache()
    configure_jobs(db_path, result_cache)

    # Ensure the secondmate namespace exists for result storage
    try:
        spark.sql("CREATE NAMESPACE IF NOT EXISTS user.secondmate")
    except Exception:
        logger.warning("Could not create users.secondmate namespace", exc_info=True)

    # Start the background job runner
    runner_task = asyncio.create_task(
        run_job_loop(db_path, get_spark_provider, result_cache)
    )

    yield

    # Shutdown: cancel the runner
    runner_task.cancel()
    try:
        await runner_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="SecondMate Backend", lifespan=lifespan)
router = APIRouter()

# Note: The synchronous /query/execute endpoint has been replaced by the
# async job queue system. Use POST /api/jobs/submit to submit queries.

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
    """List tables and views in a specific namespace."""
    validate_identifier(catalog_name)
    validate_identifier(namespace)
    try:
        items_dict = {}

        # 1. Get Tables (which also includes views, but we'll flag them as tables initially)
        df_tables = spark.sql(f"SHOW TABLES IN {catalog_name}.{namespace}")
        for row in df_tables.collect():
            items_dict[row.tableName] = "table"

        # 2. Get Views (to override the type of views)
        try:
            df_views = spark.sql(f"SHOW VIEWS IN {catalog_name}.{namespace}")
            for row in df_views.collect():
                items_dict[row.viewName] = "view"
        except Exception as e:
            logger.debug(f"Views not supported for {catalog_name}.{namespace}: {e}")

        items = [{"name": name, "type": type} for name, type in items_dict.items()]
        return {"items": items}
    except Exception:
        logger.error(f"Error retrieving tables for {catalog_name}.{namespace}", exc_info=True)
        return {"tables": [], "error": "Unable to retrieve tables."}

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
                        items_dict = {}
                        df_tables = spark.sql(f"SHOW TABLES IN {cat}.{ns}")
                        for row in df_tables.collect():
                            items_dict[row.tableName] = "table"

                        # 4. Search Views within Namespace (override type)
                        try:
                            df_views = spark.sql(f"SHOW VIEWS IN {cat}.{ns}")
                            for row in df_views.collect():
                                items_dict[row.viewName] = "view"
                        except Exception as e:
                            logger.debug(f"Views not supported for {cat}.{ns}: {e}")

                        for name, item_type in items_dict.items():
                            if query in name.lower():
                                results.append({
                                    "type": item_type, 
                                    "catalog": cat, 
                                    "namespace": ns, 
                                    "table": name,
                                    "name": name
                                })
                    except Exception:
                        continue # Ignore individual failures
            except Exception:
                continue

    except Exception:
        logger.error("Error during catalog search", exc_info=True)
        return {"results": [], "error": "An error occurred during search."}

    return {"results": results}

# Include the API routers
app.include_router(router, prefix="/api")
app.include_router(table_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")

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
