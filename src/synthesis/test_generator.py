import json
from typing import Any, Dict

class TestGenerator:
    """
    Generates pytest code to validate data against a schema.
    """
    
    def generate_test_code(self, target_type: str, schema: Dict[str, Any]) -> str:
        """
        Generates a python string containing pytest functions.
        """
        schema_json = json.dumps(schema)
        
        code = f"""
import pytest
import json
import sys

# Target Schema
SCHEMA = {schema_json}

def validate_schema(data, schema):
    if schema.get("type") == "array":
        assert isinstance(data, list), "Output must be a list"
        if "items" in schema:
            for item in data:
                validate_schema(item, schema["items"])
    elif schema.get("type") == "object":
        assert isinstance(data, dict), "Output must be a dictionary"
        if "properties" in schema:
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    validate_schema(data[prop], prop_schema)
                # Note: We are not strictly enforcing required fields here for simplicity, 
                # but we could if 'required' list exists.
                
    elif schema.get("type") == "string":
        assert isinstance(data, str), "Output must be a string"
    elif schema.get("type") == "integer":
        assert isinstance(data, int), "Output must be an integer"
    # Add more types as needed

def test_output_schema():
    # This function will be called by the runner with the actual result
    # But wait, pytest usually runs on files.
    # We need a way to pass the result to the test.
    # Strategy: The runner saves the result to 'result.json', and the test reads it.
    
    try:
        with open("result.json", "r") as f:
            result = json.load(f)
    except FileNotFoundError:
        pytest.fail("result.json not found")
        
    validate_schema(result, SCHEMA)
    
    # Specific checks for Knowledge Graph
    if "{target_type}" == "KGTriples":
        assert len(result) > 0, "Knowledge Graph should not be empty"
        for triple in result:
            assert "subject" in triple
            assert "predicate" in triple
            assert "object" in triple
"""
        return code
