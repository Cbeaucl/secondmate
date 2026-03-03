from enum import Enum
from typing import List, Any, Optional, Dict
from pydantic import BaseModel

class DataType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"

class UiInputType(str, Enum):
    TEXT = "text"
    SELECT = "select"
    RADIO = "radio"
    TOGGLE = "toggle"

class ConfigOptionItem(BaseModel):
    label: str
    value: Any

class ConfigOption(BaseModel):
    id: str
    label: str
    data_type: DataType
    ui_input_type: UiInputType
    current_value: Optional[Any] = None
    default_value: Optional[Any] = None
    options: Optional[List[ConfigOptionItem]] = None
    is_required: bool = False
