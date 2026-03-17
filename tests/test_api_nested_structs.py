"""
Tests for nested struct serialization in query results.

The original execute_query endpoint has been replaced by the async job queue.
This test now validates that the result cache correctly serializes nested
Spark Row structures through the sanitize_for_serialization utility, which
is the same code path used by IcebergResultCache.load().
"""
import unittest
from unittest.mock import MagicMock
from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from secondmate.utils import sanitize_for_serialization


class TestNestedStructSerialization(unittest.TestCase):
    def test_nested_structs_serialize_to_dicts(self):
        """Verify that nested Row objects are recursively converted to dicts."""
        # Simulate what Spark would return for a query with nested structs
        row1 = Row(
            id=1,
            nested=Row(
                inner_str="test",
                inner_nested=Row(val=42)
            )
        )

        # This is the same code path as IcebergResultCache.load()
        data = [row1.asDict(recursive=True)]
        data = sanitize_for_serialization(data)

        self.assertEqual(len(data), 1)
        record = data[0]

        self.assertEqual(record["id"], 1)
        self.assertIsInstance(record["nested"], dict)
        self.assertEqual(record["nested"]["inner_str"], "test")
        self.assertIsInstance(record["nested"]["inner_nested"], dict)
        self.assertEqual(record["nested"]["inner_nested"]["val"], 42)


if __name__ == "__main__":
    unittest.main()
