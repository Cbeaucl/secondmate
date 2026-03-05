import unittest
from unittest.mock import MagicMock, patch
from secondmate.main import get_table_overview

class TestTableOverview(unittest.TestCase):
    @patch("secondmate.main.get_spark_provider")
    def test_get_table_overview_unpartitioned(self, mock_get_spark_provider):
        mock_spark = MagicMock()
        mock_provider = MagicMock()
        mock_provider.get_session.return_value = mock_spark
        mock_get_spark_provider.return_value = mock_provider

        # Mock df for schema
        mock_df = MagicMock()
        mock_spark.table.return_value = mock_df
        mock_df.schema.jsonValue.return_value = {"fields": []}

        # Mock metadata queries
        def mock_sql(query):
            m_df = MagicMock()
            if ".properties" in query or "SHOW TBLPROPERTIES" in query:
                m_df.collect.return_value = []
            elif ".snapshots" in query:
                m_df.collect.return_value = []
            elif ".partitions" in query:
                # Unpartitioned table has no rows in partitions metadata table
                m_df.collect.return_value = []
            elif ".files" in query:
                # Unpartitioned table HAS rows in files metadata table
                row = MagicMock()
                # Mock asDict to return a dict with an empty partition struct
                row.asDict.return_value = {
                    "content": 0,
                    "file_format": "PARQUET",
                    "spec_id": 0,
                    "partition": {}, # Empty struct for unpartitioned
                    "record_count": 100,
                    "file_size_in_bytes": 1.5 * 1024 * 1024,
                    "file_path": "s3://bucket/table/data.parquet"
                }
                m_df.collect.return_value = [row]
            return m_df

        mock_spark.sql.side_effect = mock_sql

        result = get_table_overview("catalog", "ns", "table", spark=mock_spark)

        self.assertEqual(result["tableName"], "catalog.ns.table")
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0]["partition"], {})
        self.assertEqual(result["files"][0]["file_size_mb"], 1.5)
        self.assertNotIn("file_path", result["files"][0])

if __name__ == "__main__":
    unittest.main()
