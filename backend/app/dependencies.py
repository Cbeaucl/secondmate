from functools import lru_cache
from pyspark.sql import SparkSession
from fastapi import Depends
from app.providers.spark_interface import SparkProvider
from app.providers.local_spark import LocalSparkProvider

@lru_cache()
def get_spark_provider() -> SparkProvider:
    # In the future, this can be swapped based on config
    return LocalSparkProvider()

def get_spark_session(
    provider: SparkProvider = Depends(get_spark_provider)
) -> SparkSession:
    return provider.get_session()
