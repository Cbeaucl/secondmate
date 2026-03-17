
import unittest
from unittest.mock import MagicMock
from secondmate.main import get_catalogs, get_namespaces, get_tables, search_catalog

class TestSecurityFixes(unittest.TestCase):
    def setUp(self):
        self.mock_spark = MagicMock()
        self.mock_provider = MagicMock()
        self.mock_provider.get_session.return_value = self.mock_spark
        self.mock_provider.get_configs.return_value = []
        self.sensitive_info = "Sensitive Path: /etc/passwd"
        self.exception = Exception(f"Database error: {self.sensitive_info}")

    # Note: execute_query has been replaced by the async job queue system.
    # Security for query execution errors is now handled by the job runner,
    # which stores error messages in the SQLite queue (tested in test_runner.py).

    def test_get_catalogs_secure(self):
        self.mock_spark.sql.side_effect = self.exception

        response = get_catalogs(spark=self.mock_spark)

        self.assertIn("error", response)
        self.assertEqual(response["error"], "Unable to retrieve catalogs.")
        self.assertNotIn(self.sensitive_info, response["error"])

    def test_get_namespaces_secure(self):
        self.mock_spark.sql.side_effect = self.exception

        response = get_namespaces("test_catalog", spark=self.mock_spark)

        self.assertIn("error", response)
        self.assertEqual(response["error"], "Unable to retrieve namespaces.")
        self.assertNotIn(self.sensitive_info, response["error"])

    def test_get_tables_secure(self):
        self.mock_spark.sql.side_effect = self.exception

        response = get_tables("test_catalog", "test_namespace", spark=self.mock_spark)

        self.assertIn("error", response)
        self.assertEqual(response["error"], "Unable to retrieve tables.")
        self.assertNotIn(self.sensitive_info, response["error"])

    def test_search_catalog_secure(self):
        self.mock_spark.sql.side_effect = self.exception

        response = search_catalog("search_term", spark=self.mock_spark)

        self.assertIn("error", response)
        self.assertEqual(response["error"], "An error occurred during search.")
        self.assertNotIn(self.sensitive_info, response["error"])

if __name__ == "__main__":
    unittest.main()
