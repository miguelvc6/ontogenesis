from typing import List, Dict, Any
import networkx as nx
from .types import DataType
from .tools import Tool

class CapabilityGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_type(self, type_node: DataType):
        self.graph.add_node(type_node.name, schema=type_node.schema_def)

    def add_tool(self, tool: Tool):
        self.graph.add_edge(tool.input_type, tool.output_type, tool=tool)

    def find_path(self, start_type: str, end_type: str) -> List[str]:
        try:
            return nx.shortest_path(self.graph, start_type, end_type)
        except nx.NetworkXNoPath:
            return []

    def detect_gap(self, start_type: str, end_type: str) -> Dict[str, Any]:
        """
        A simple gap detector:
        If no path exists, we simply propose a direct edge.
        """
        if not self.find_path(start_type, end_type):
            return {
                "gap": True,
                "source": start_type,
                "target": end_type
            }
        return {"gap": False}
