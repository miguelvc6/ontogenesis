import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from execution.runner import CodeRunner

def test_run_simple_function():
    runner = CodeRunner()
    code = """
def add(a, b):
    return a + b
"""
    result = runner.run_code(code, "add", a=5, b=3)
    assert result == 8

def test_run_function_with_imports():
    runner = CodeRunner()
    code = """
import json
def to_json(data):
    return json.dumps(data)
"""
    result = runner.run_code(code, "to_json", data={"key": "value"})
    assert result == '{"key": "value"}'

def test_missing_entry_point():
    runner = CodeRunner()
    code = """
def foo():
    pass
"""
    with pytest.raises(ValueError, match="Entry point 'bar' not found"):
        runner.run_code(code, "bar")

def test_execution_error():
    runner = CodeRunner()
    code = """
def crash():
    raise ValueError("Boom")
"""
    with pytest.raises(RuntimeError, match="Failed to execute entry point"):
        runner.run_code(code, "crash")
