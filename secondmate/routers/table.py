from fastapi import APIRouter, Depends, HTTPException
from pyspark.sql import SparkSession
from secondmate.dependencies import get_spark_session
from secondmate.utils import validate_identifier, sanitize_for_serialization
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_full_table_name(catalog_name: str, namespace: str, table_name: str) -> str:
    validate_identifier(catalog_name)
    validate_identifier(namespace)
    validate_identifier(table_name)
    return f"{catalog_name}.{namespace}.{table_name}"

def _get_metadata(spark: SparkSession, full_table_name: str, suffix: str, query: str = None):
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

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/schema")
def get_schema(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    full_table_name = get_full_table_name(catalog_name, namespace, table_name)
    try:
        df = spark.table(full_table_name)
        return df.schema.jsonValue()
    except Exception as e:
        logger.error(f"Error retrieving schema for {full_table_name}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/ddl")
def get_ddl(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    full_table_name = get_full_table_name(catalog_name, namespace, table_name)
    try:
        df = spark.sql(f"SHOW CREATE TABLE {full_table_name}")
        ddl = df.collect()[0][0]
        return {"ddl": ddl}
    except Exception as e:
        logger.error(f"Error retrieving DDL for {full_table_name}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/properties")
def get_properties(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    full_table_name = get_full_table_name(catalog_name, namespace, table_name)
    return _get_metadata(spark, full_table_name, "properties", f"SHOW TBLPROPERTIES {full_table_name}")

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/snapshots")
def get_snapshots(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    full_table_name = get_full_table_name(catalog_name, namespace, table_name)
    return _get_metadata(spark, full_table_name, "snapshots", f"SELECT * FROM {full_table_name}.snapshots ORDER BY committed_at DESC LIMIT 250")

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/partitions")
def get_partitions(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    full_table_name = get_full_table_name(catalog_name, namespace, table_name)
    return _get_metadata(spark, full_table_name, "partitions", f"SELECT * FROM {full_table_name}.partitions LIMIT 250")

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/files")
def get_files(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    full_table_name = get_full_table_name(catalog_name, namespace, table_name)
    partition_col = ""
    try:
        if "partition" in spark.table(f"{full_table_name}.files").columns:
            partition_col = "partition,"
    except Exception:
        pass

    query = f"""
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
    """
    return _get_metadata(spark, full_table_name, "files", query)

@router.get("/catalogs/{catalog_name}/namespaces/{namespace}/tables/{table_name}/metrics")
def get_metrics(catalog_name: str, namespace: str, table_name: str, spark: SparkSession = Depends(get_spark_session)):
    full_table_name = get_full_table_name(catalog_name, namespace, table_name)
    
    last_snapshot = "N/A"
    earliest_snapshot = "N/A"
    row_count = "N/A"
    
    try:
        snap_df = spark.sql(f"SELECT min(committed_at) as earliest, max(committed_at) as latest FROM {full_table_name}.snapshots")
        row = snap_df.collect()[0]
        if row.latest:
            last_snapshot = str(row.latest)
        if row.earliest:
            earliest_snapshot = str(row.earliest)
            
        latest_snap_df = spark.sql(f"SELECT summary FROM {full_table_name}.snapshots ORDER BY committed_at DESC LIMIT 1")
        if latest_snap_df.count() > 0:
            summary = latest_snap_df.collect()[0].summary
            if summary and "total-records" in summary:
                val = int(summary["total-records"])
                row_count = f"{val:,}"
    except Exception:
        pass
        
    avg_file_size = "N/A"
    try:
        files_df = spark.sql(f"SELECT sum(record_count) as total_records, sum(file_size_in_bytes) as total_size, count(1) as file_count FROM {full_table_name}.files")
        row = files_df.collect()[0]
        
        if row_count == "N/A" and row.total_records is not None:
            row_count = f"{int(row.total_records):,}"
            
        if row.total_size is not None and row.file_count and row.file_count > 0:
            avg_mb = (row.total_size / (1024.0 * 1024.0)) / row.file_count
            avg_file_size = f"{avg_mb:.2f} MB"
            
    except Exception:
        pass
        
    column_count = "N/A"
    try:
        df = spark.table(full_table_name)
        column_count = str(len(df.schema.fields))
    except Exception:
        pass
        
    partition_columns = "N/A"
    try:
        parts_df = spark.sql(f"SELECT * FROM {full_table_name}.partitions LIMIT 1")
        if parts_df.count() > 0:
            row_dict = parts_df.collect()[0].asDict(recursive=True)
            if "partition" in row_dict and isinstance(row_dict["partition"], dict):
                keys = list(row_dict["partition"].keys())
                if keys:
                    partition_columns = ", ".join(keys)
    except Exception:
        pass

    return {
        "last_snapshot": last_snapshot,
        "earliest_snapshot": earliest_snapshot,
        "row_count": row_count,
        "column_count": column_count,
        "avg_file_size": avg_file_size,
        "partition_columns": partition_columns
    }
