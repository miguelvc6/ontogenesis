from typing import List, Dict, Any
import os
import networkx as nx
import matplotlib.pyplot as plt
from .types import DataType
from .tools import Tool
from utils.tracer import tracer

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
        tracer.start_span("detect_gap", {"start_type": start_type, "end_type": end_type})
        
        if not self.find_path(start_type, end_type):
            result = {
                "gap": True,
                "source": start_type,
                "target": end_type
            }
            tracer.end_span(outputs=result)
            return result
            
        result = {"gap": False}
        tracer.end_span(outputs=result)
        return result

    def visualize(self, output_path: str = "ontology_graph.png"):
        """
        Visualizes the ontology graph and saves it to a file.
        """
        tracer.start_span("visualize_graph", {"output_path": output_path})
        try:
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(self.graph)
            
            # Draw nodes
            nx.draw_networkx_nodes(self.graph, pos, node_size=2000, node_color='lightblue')
            nx.draw_networkx_labels(self.graph, pos)
            
            # Draw edges
            nx.draw_networkx_edges(self.graph, pos, edge_color='gray', arrows=True)
            edge_labels = {
                (u, v): d['tool'].name 
                for u, v, d in self.graph.edges(data=True) 
                if 'tool' in d
            }
            nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels)
            
            plt.title("OntoGenesis Capability Graph")
            plt.axis('off')
            plt.savefig(output_path)
            plt.close()
            tracer.end_span(outputs="Graph saved")
        except Exception as e:
            tracer.end_span(error=str(e))
            print(f"Visualization failed: {e}")

    def save_to_json(self, path: str):
        """Saves the graph state to a JSON file."""
        tracer.start_span("save_graph", {"path": path})
        data = {
            "nodes": [],
            "edges": []
        }
        
        for node, attrs in self.graph.nodes(data=True):
            data["nodes"].append({
                "name": node,
                "schema": attrs.get("schema", {})
            })
            
        for u, v, attrs in self.graph.edges(data=True):
            if "tool" in attrs:
                tool: Tool = attrs["tool"]
                data["edges"].append({
                    "source": u,
                    "target": v,
                    "tool": tool.model_dump()
                })
        
        import json
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        tracer.end_span(outputs="Graph saved to JSON")

    def load_from_json(self, path: str):
        """Loads the graph state from a JSON file."""
        tracer.start_span("load_graph", {"path": path})
        import json
        if not os.path.exists(path):
            tracer.end_span(error="File not found")
            return

        with open(path, "r") as f:
            data = json.load(f)
            
        self.graph.clear()
        
        for node_data in data["nodes"]:
            self.add_type(DataType(name=node_data["name"], schema_def=node_data["schema"]))
            
        for edge_data in data["edges"]:
            tool_data = edge_data["tool"]
            tool = Tool(**tool_data)
            self.add_tool(tool)
            
        tracer.end_span(outputs="Graph loaded from JSON")
