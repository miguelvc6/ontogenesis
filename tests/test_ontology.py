import pytest
import sys
import os

# Add src to python path to make sure tests can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from ontology.graph import CapabilityGraph
from ontology.types import DataType
from ontology.tools import Tool

def test_graph_initialization():
    graph = CapabilityGraph()
    assert graph is not None

def test_add_type():
    graph = CapabilityGraph()
    dt = DataType(name="PDF", schema_def={"type": "file", "format": "pdf"})
    graph.add_type(dt)
    assert "PDF" in graph.graph.nodes

def test_gap_detection():
    graph = CapabilityGraph()
    pdf = DataType(name="PDF", schema_def={})
    text = DataType(name="Text", schema_def={})
    graph.add_type(pdf)
    graph.add_type(text)
    
    # No tool yet
    gap = graph.detect_gap("PDF", "Text")
    assert gap["gap"] is True
    
    # Add tool
    tool = Tool(name="pdf_to_text", input_type="PDF", output_type="Text")
    graph.add_tool(tool)
    
    gap = graph.detect_gap("PDF", "Text")
    assert gap["gap"] is False
