import unittest
from unittest.mock import MagicMock
from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from secondmate.main import execute_query, QueryRequest

class TestApiNestedStructs(unittest.TestCase):
    def test_execute_query_with_nested_structs(self):
        # Setup mock spark and dataframe
        mock_spark = MagicMock()
        mock_df = MagicMock()
        mock_spark.sql.return_value = mock_df
        mock_df.limit.return_value = mock_df

        # Mock schema
        mock_field1 = MagicMock()
        mock_field1.name = "id"
        mock_field1.dataType = IntegerType()

        mock_field2 = MagicMock()
        mock_field2.name = "nested"
        mock_field2.dataType = StructType([
            StructField("inner_str", StringType()),
            StructField("inner_nested", StructType([
                StructField("val", IntegerType())
            ]))
        ])

        mock_schema = MagicMock()
        mock_schema.fields = [mock_field1, mock_field2]
        mock_df.schema = mock_schema

        # Mock data with nested Rows
        row1 = Row(
            id=1,
            nested=Row(
                inner_str="test",
                inner_nested=Row(val=42)
            )
        )
        mock_df.collect.return_value = [row1]

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.get_session.return_value = mock_spark
        mock_provider.get_configs.return_value = []

        # Execute request
        request = QueryRequest(query="SELECT * FROM test_table")
        response = execute_query(request, provider=mock_provider)

        # Verify schema is correct (stringified types for JSON serialization)
        self.assertEqual(len(response["schema"]), 2)
        self.assertEqual(response["schema"][0]["name"], "id")
        self.assertEqual(response["schema"][1]["name"], "nested")

        # Verify data is parsed recursively to pure dicts
        self.assertEqual(len(response["data"]), 1)
        data = response["data"][0]

        self.assertEqual(data["id"], 1)
        self.assertIsInstance(data["nested"], dict)
        self.assertEqual(data["nested"]["inner_str"], "test")
        self.assertIsInstance(data["nested"]["inner_nested"], dict)
        self.assertEqual(data["nested"]["inner_nested"]["val"], 42)

if __name__ == "__main__":
    unittest.main()
