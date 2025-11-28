from typing import List
from pydantic import BaseModel

class Tool(BaseModel):
    """Represents a Capability (Edge)"""
    name: str
    input_type: str
    output_type: str
    constraints: List[str] = []
    code: str = "" # The actual implementation
