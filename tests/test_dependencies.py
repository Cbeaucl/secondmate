import os
import unittest
from unittest.mock import patch, MagicMock
from secondmate.dependencies import get_spark_provider, get_spark_session
from secondmate.providers.local_spark import LocalSparkProvider
from secondmate.providers.spark_interface import SparkProvider
from pyspark.sql import SparkSession

class TestSparkProvider(unittest.TestCase):
    def setUp(self):
        # Clear the cache before each test to ensure fresh execution
        get_spark_provider.cache_clear()

    def tearDown(self):
        # Clear the cache after each test to avoid side effects
        get_spark_provider.cache_clear()

    def test_default_provider(self):
        """Test that LocalSparkProvider is returned when SPARK_PROVIDER_CLASS is not set."""
        with patch.dict(os.environ, {}, clear=True):
            provider = get_spark_provider()
            self.assertIsInstance(provider, LocalSparkProvider)

    def test_custom_provider_success(self):
        """Test that a valid custom provider is loaded and returned."""
        # Create a mock provider class
        mock_provider_class = MagicMock(spec=SparkProvider)
        mock_provider_instance = mock_provider_class.return_value
        # Ensure it has get_session method
        mock_provider_instance.get_session = MagicMock(return_value=MagicMock(spec=SparkSession))

        # Patch importlib to return our mock module
        with patch.dict(os.environ, {"SPARK_PROVIDER_CLASS": "my.custom.Provider"}), \
             patch("importlib.import_module") as mock_import:

            mock_module = MagicMock()
            setattr(mock_module, "Provider", mock_provider_class)
            mock_import.return_value = mock_module

            provider = get_spark_provider()

            mock_import.assert_called_with("my.custom")
            mock_provider_class.assert_called_once()
            self.assertEqual(provider, mock_provider_instance)

    def test_custom_provider_attribute_error(self):
        """Test that ImportError is raised if the class cannot be found in the module."""
        with patch.dict(os.environ, {"SPARK_PROVIDER_CLASS": "os.FakeProviderClass"}):
            with self.assertRaises(ImportError) as cm:
                get_spark_provider()

            self.assertIn("Could not load Spark provider 'os.FakeProviderClass'", str(cm.exception))

    def test_custom_provider_import_error(self):
        """Test that ImportError is raised if the module cannot be imported."""
        with patch.dict(os.environ, {"SPARK_PROVIDER_CLASS": "invalid.module.Provider"}), \
             patch("importlib.import_module", side_effect=ImportError("Module not found")):

            with self.assertRaises(ImportError) as cm:
                get_spark_provider()

            self.assertIn("Could not load Spark provider 'invalid.module.Provider'", str(cm.exception))

    def test_custom_provider_missing_method(self):
        """Test that ImportError (wrapping ValueError) is raised if provider lacks get_session."""
        class BadProvider:
            pass

        with patch.dict(os.environ, {"SPARK_PROVIDER_CLASS": "bad.Provider"}), \
             patch("importlib.import_module") as mock_import:

            mock_module = MagicMock()
            mock_module.Provider = BadProvider
            mock_import.return_value = mock_module

            with self.assertRaises(ImportError) as cm:
                get_spark_provider()

            self.assertIn("must implement 'get_session' method", str(cm.exception))

    def test_custom_provider_malformed_string(self):
        """Test that ImportError is raised if SPARK_PROVIDER_CLASS is malformed."""
        with patch.dict(os.environ, {"SPARK_PROVIDER_CLASS": "InvalidStringNoDot"}):
             with self.assertRaises(ImportError) as cm:
                get_spark_provider()
             # The error message from split will be in the cause
             # But our code catches ValueError and re-raises as ImportError with specific message
             self.assertIn("Could not load Spark provider 'InvalidStringNoDot'", str(cm.exception))

    def test_get_spark_session(self):
        """Test that get_spark_session calls get_session on the provider."""
        mock_provider = MagicMock(spec=SparkProvider)
        mock_session = MagicMock(spec=SparkSession)
        mock_provider.get_session.return_value = mock_session

        session = get_spark_session(mock_provider)

        mock_provider.get_session.assert_called_once()
        self.assertEqual(session, mock_session)

if __name__ == '__main__':
    unittest.main()
