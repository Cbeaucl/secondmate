import re
import base64
from fastapi import HTTPException

def sanitize_for_serialization(obj):
    if isinstance(obj, dict):
        return {str(k): sanitize_for_serialization(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_serialization(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_for_serialization(v) for v in obj)
    elif isinstance(obj, (bytes, bytearray)):
        try:
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            return base64.b64encode(obj).decode('utf-8')
    return obj

def validate_identifier(name: str):
    """Validate that an identifier only contains alphanumeric characters, underscores, and dots."""
    if not re.match(r"^[a-zA-Z0-9_.]+\Z", name):
        raise HTTPException(status_code=400, detail=f"Invalid identifier: {name}")
