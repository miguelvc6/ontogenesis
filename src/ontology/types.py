from typing import Dict, Any
from pydantic import BaseModel

class DataType(BaseModel):
    """Represents a Data Type in the Ontology"""
    name: str
    schema_def: Dict[str, Any]  # JSON Schema or Python Type hint
