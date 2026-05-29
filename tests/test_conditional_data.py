import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from secondmate.providers.spark_interface import SparkProvider
from secondmate.providers.local_spark import LocalSparkProvider


def create_mock_provider(is_local: bool):
    if is_local:
        provider = LocalSparkProvider()
    else:
        class OtherProvider(SparkProvider):
            def get_session(self): return MagicMock()
        provider = OtherProvider()

    provider.get_session = MagicMock()
    mock_spark = MagicMock()
    provider.get_session.return_value = mock_spark

    # Setup mock spark behavior to track calls
    mock_spark.catalog.tableExists.return_value = False  # Always say table doesn't exist so it tries to create
    mock_spark.table.return_value.count.return_value = 0

    # Mock SHOW NAMESPACES to always return a dummy list so initialize passes
    mock_res = MagicMock()
    mock_res.collect.return_value = [MagicMock()]
    mock_spark.sql.return_value = mock_res

    return provider, mock_spark


@pytest.mark.asyncio
async def test_conditional_data_local_spark_provider():
    provider_local, spark_local = create_mock_provider(is_local=True)

    with patch("secondmate.main.get_spark_provider", return_value=provider_local):
        from secondmate.main import lifespan
        app = FastAPI()

        async with lifespan(app):
            pass

    # Check if table creation was attempted
    # We expect calls to create_table_if_not_exists -> spark.sql("CREATE TABLE ...")
    create_calls = [call for call in spark_local.sql.mock_calls if "CREATE TABLE" in str(call)]

    assert len(create_calls) > 0, "No tables created for LocalSparkProvider"


@pytest.mark.asyncio
async def test_conditional_data_other_provider():
    provider_other, spark_other = create_mock_provider(is_local=False)

    with patch("secondmate.main.get_spark_provider", return_value=provider_other):
        from secondmate.main import lifespan
        app = FastAPI()

        async with lifespan(app):
            pass

    create_calls_other = [call for call in spark_other.sql.mock_calls if "CREATE TABLE" in str(call)]

    assert len(create_calls_other) == 0, f"Tables WERE created for OtherProvider! Count: {len(create_calls_other)}"
