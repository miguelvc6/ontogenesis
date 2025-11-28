import pytest
import os
import json
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from ontology.graph import CapabilityGraph
from ontology.types import DataType
from ontology.tools import Tool

def test_save_load_graph(tmp_path):
    # 1. Setup Graph
    graph = CapabilityGraph()
    graph.add_type(DataType(name="TypeA", schema_def={"type": "string"}))
    graph.add_type(DataType(name="TypeB", schema_def={"type": "integer"}))
    
    tool = Tool(name="tool_a_to_b", input_type="TypeA", output_type="TypeB")
    graph.add_tool(tool)
    
    # 2. Save
    save_path = tmp_path / "graph.json"
    graph.save_to_json(str(save_path))
    
    assert os.path.exists(save_path)
    
    # 3. Load into new graph
    new_graph = CapabilityGraph()
    new_graph.load_from_json(str(save_path))
    
    # 4. Verify
    assert "TypeA" in new_graph.graph.nodes
    assert "TypeB" in new_graph.graph.nodes
    assert new_graph.graph.has_edge("TypeA", "TypeB")
    
    edge_data = new_graph.graph.get_edge_data("TypeA", "TypeB")
    loaded_tool = edge_data["tool"]
    assert loaded_tool.name == "tool_a_to_b"
    assert loaded_tool.input_type == "TypeA"
    assert loaded_tool.output_type == "TypeB"
