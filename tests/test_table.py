import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException
from secondmate.routers.table import (
    get_schema,
    get_properties,
    get_snapshots,
    get_partitions,
    get_files,
    get_metrics
)
from pyspark.sql import Row

class TestTableRouter(unittest.TestCase):
    def setUp(self):
        self.mock_spark = MagicMock()
        self.catalog = "local"
        self.namespace = "default"
        self.table = "test_table"

    def test_get_schema_success(self):
        mock_df = MagicMock()
        mock_schema = MagicMock()
        mock_schema.jsonValue.return_value = {"type": "struct", "fields": []}
        mock_df.schema = mock_schema
        self.mock_spark.table.return_value = mock_df

        result = get_schema(self.catalog, self.namespace, self.table, spark=self.mock_spark)
        self.assertEqual(result, {"type": "struct", "fields": []})
        self.mock_spark.table.assert_called_with("local.default.test_table")

    def test_get_properties_success(self):
        mock_df = MagicMock()
        # Row needs to be converted properly by asDict
        mock_df.collect.return_value = [Row(key="test_key", value="test_val")]
        self.mock_spark.sql.return_value = mock_df

        result = get_properties(self.catalog, self.namespace, self.table, spark=self.mock_spark)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["key"], "test_key")
        self.mock_spark.sql.assert_called_with("SHOW TBLPROPERTIES local.default.test_table")
        
    def test_get_metrics_success(self):
        mock_snap_df = MagicMock()
        mock_snap_df.collect.return_value = [Row(earliest="2023-01-01", latest="2023-01-02")]
        
        mock_latest_snap_df = MagicMock()
        mock_latest_snap_df.count.return_value = 1
        mock_latest_snap_df.collect.return_value = [Row(summary={"total-records": "100"})]
        
        mock_files_df = MagicMock()
        mock_files_df.collect.return_value = [Row(total_records=100, total_size=1048576, file_count=1)]
        
        mock_table_df = MagicMock()
        mock_table_df.schema.fields = [1, 2, 3] # 3 columns
        
        mock_parts_df = MagicMock()
        mock_parts_df.count.return_value = 1
        mock_parts_df.collect.return_value = [Row(partition={"day": "2023-01-01"})]
        
        def sql_side_effect(query):
            if "min(committed_at)" in query:
                return mock_snap_df
            elif "ORDER BY committed_at DESC LIMIT 1" in query:
                return mock_latest_snap_df
            elif "sum(record_count)" in query:
                return mock_files_df
            elif "partitions LIMIT 1" in query:
                return mock_parts_df
            return MagicMock()

        self.mock_spark.sql.side_effect = sql_side_effect
        self.mock_spark.table.return_value = mock_table_df
        
        result = get_metrics(self.catalog, self.namespace, self.table, spark=self.mock_spark)
        
        self.assertEqual(result["last_snapshot"], "2023-01-02")
        self.assertEqual(result["row_count"], "100")
        self.assertEqual(result["column_count"], "3")
        self.assertEqual(result["avg_file_size"], "1.00 MB")
        self.assertEqual(result["partition_columns"], "day")

if __name__ == "__main__":
    unittest.main()
