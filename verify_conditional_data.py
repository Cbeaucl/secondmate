import asyncio
import sys
from unittest.mock import MagicMock, patch
from secondmate.providers.spark_interface import SparkProvider
from secondmate.providers.local_spark import LocalSparkProvider

# Mock the entire secondmate.main module dependencies before importing it
# because we want to intercept get_spark_provider at module level if possible,
# or we can patch it.

async def run_verification():
    print("Starting verification...")

    # helper to mock provider
    def create_mock_provider(is_local: bool):
        if is_local:
            provider = MagicMock(spec=LocalSparkProvider)
            # Make sure isinstance(provider, LocalSparkProvider) returns True
            # MagicMock(spec=...) usually handles this, but since we are mocking the class itself sometimes...
            # Actually, standard MagicMock(spec=LocalSparkProvider) works for isinstance checks if class is real.
            # But let's be safe: we will create a real LocalSparkProvider or a subclass if needed.
            # Actually, for the test to work, we need `isinstance(provider, LocalSparkProvider)` to be true.
            provider = LocalSparkProvider() 
        else:
            class OtherProvider(SparkProvider):
                def get_session(self): return MagicMock()
            provider = OtherProvider()
        
        provider.get_session = MagicMock()
        mock_spark = MagicMock()
        provider.get_session.return_value = mock_spark
        
        # Setup mock spark behavior to track calls
        mock_spark.catalog.tableExists.return_value = False # Always say table doesn't exist so it tries to create
        mock_spark.table.return_value.count.return_value = 0
        
        return provider, mock_spark

    # 1. Test with LocalSparkProvider
    print("\n--- Test Case 1: LocalSparkProvider ---")
    provider_local, spark_local = create_mock_provider(is_local=True)
    
    with patch("secondmate.main.get_spark_provider", return_value=provider_local):
        from secondmate.main import lifespan
        from fastapi import FastAPI
        app = FastAPI()
        
        async with lifespan(app):
            pass
            
    # Check if table creation was attempted
    # We expect calls to create_table_if_not_exists -> spark.sql("CREATE TABLE ...")
    create_calls = [call for call in spark_local.sql.mock_calls if "CREATE TABLE" in str(call)]
    if create_calls:
        print(f"SUCCESS: specific tables created as expected. Count: {len(create_calls)}")
    else:
        print("FAILURE: No tables created for LocalSparkProvider")

    # 2. Test with OtherProvider
    print("\n--- Test Case 2: OtherProvider ---")
    provider_other, spark_other = create_mock_provider(is_local=False)
    
    # We need to re-import or verify that 'lifespan' uses the new mock. 
    # Since we patched 'secondmate.main.get_spark_provider', it should work.
    
    with patch("secondmate.main.get_spark_provider", return_value=provider_other):
        async with lifespan(app):
            pass

    create_calls_other = [call for call in spark_other.sql.mock_calls if "CREATE TABLE" in str(call)]
    if not create_calls_other:
        print("SUCCESS: No tables created for OtherProvider")
    else:
        print(f"FAILURE: Tables WERE created for OtherProvider! Count: {len(create_calls_other)}")

if __name__ == "__main__":
    asyncio.run(run_verification())
