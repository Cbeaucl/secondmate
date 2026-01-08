import os
import importlib
from functools import lru_cache
from pyspark.sql import SparkSession
from fastapi import Depends, HTTPException
from secondmate.providers.spark_interface import SparkProvider
from secondmate.providers.local_spark import LocalSparkProvider

@lru_cache()
def get_spark_provider() -> SparkProvider:
    provider_class_path = os.getenv("SPARK_PROVIDER_CLASS")
    
    if not provider_class_path:
        return LocalSparkProvider()
    
    try:
        module_name, class_name = provider_class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        provider_cls = getattr(module, class_name)
        
        # Instantiate the provider. 
        # We assume it takes no arguments or we might need to support passing args via env vars too.
        # For now, let's assume valid providers typically don't need args or handle configuration internally.
        provider_instance = provider_cls()
        
        if not hasattr(provider_instance, "get_session"):
             raise ValueError(f"Provider '{provider_class_path}' must implement 'get_session' method.")

        return provider_instance
        
    except (ImportError, AttributeError, ValueError) as e:
        # Raise a clear error if the configured provider cannot be loaded
        raise ImportError(f"Could not load Spark provider '{provider_class_path}': {e}") from e

def get_spark_session(
    provider: SparkProvider = Depends(get_spark_provider)
) -> SparkSession:
    return provider.get_session()
