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
        Detects a gap between start_type and end_type using bidirectional search.
        Finds the intersection of Forward Reachable and Backward Required sets.
        """
        tracer.start_span("detect_gap", {"start_type": start_type, "end_type": end_type})
        
        # 1. Check direct path first (optimization)
        if self.find_path(start_type, end_type):
            result = {"gap": False}
            tracer.end_span(outputs=result)
            return result

        # 2. Forward Search (Reachable types from start)
        forward_reachable = self.forward_search(start_type)
        
        # 3. Backward Search (Types that can reach end)
        backward_required = self.backward_search(end_type)
        
        # 4. Find Intersection
        intersection = forward_reachable.intersection(backward_required)
        
        if intersection:
            # If there is an intersection, a path exists (should have been caught by find_path, 
            # but maybe graph state changed or find_path is simple).
            # In our case, if find_path failed but intersection exists, it's weird.
            # But let's assume if find_path failed, we truly have a gap.
            # Wait, if intersection is not empty, then there IS a path.
            # So if find_path returned False, intersection should be empty.
            pass

        # 5. Identify the "Best" Gap
        # We want to find a pair (u, v) such that u in Forward, v in Backward, 
        # and we can synthesize a tool u -> v.
        # For v1.1, we simply propose bridging the start_type to the end_type directly
        # OR bridging the closest nodes.
        
        # For now, let's keep it simple: Source is start_type, Target is end_type.
        # But we can log the reachable sets for debugging/future advanced planning.
        
        print(f"[Graph] Forward Reachable: {forward_reachable}")
        print(f"[Graph] Backward Required: {backward_required}")
        
        result = {
            "gap": True,
            "source": start_type,
            "target": end_type,
            "forward_reachable": list(forward_reachable),
            "backward_required": list(backward_required)
        }
        tracer.end_span(outputs=result)
        return result

    def forward_search(self, start_node: str) -> set:
        """Returns all nodes reachable from start_node."""
        if start_node not in self.graph:
            return set()
        return set(nx.descendants(self.graph, start_node)) | {start_node}

    def backward_search(self, end_node: str) -> set:
        """Returns all nodes that can reach end_node."""
        if end_node not in self.graph:
            return set()
        return set(nx.ancestors(self.graph, end_node)) | {end_node}

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
