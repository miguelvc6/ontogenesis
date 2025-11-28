import sys
import os
import json
from typing import List, Dict, Any

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.ontology.graph import CapabilityGraph
from src.ontology.types import DataType
from src.ontology.tools import Tool

def main():
    print("=== OntoGenesis v0: Logic Probe Simulation ===\n")

    # 1. Initialize Graph
    graph = CapabilityGraph()
    print("[1] Initialized Capability Graph.")

    # 2. Define Types based on data/ directory
    # Type 1: Server Logs (JSON)
    server_logs_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "timestamp": {"type": "string"},
                "level": {"type": "string"},
                "service": {"type": "string"},
                "message": {"type": "string"}
            }
        }
    }
    graph.add_type(DataType(name="ServerLogs", schema_def=server_logs_schema))
    print("    - Added Type: ServerLogs")

    # Type 2: Consultant Profile (HTML)
    consultant_profile_schema = {
        "type": "string",
        "format": "html",
        "description": "HTML page containing consultant profile with name, role, contact info, etc."
    }
    graph.add_type(DataType(name="ConsultantProfile", schema_def=consultant_profile_schema))
    print("    - Added Type: ConsultantProfile")

    # Type 3: Vendor List (JSON)
    vendor_list_schema = {
        "type": "object",
        "properties": {
            "vendors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "vendor_id": {"type": "string"},
                        "name": {"type": "string"}
                    }
                }
            }
        }
    }
    graph.add_type(DataType(name="VendorList", schema_def=vendor_list_schema))
    print("    - Added Type: VendorList")

    # Type 4: PDF Invoice (File)
    pdf_invoice_schema = {
        "type": "file",
        "format": "pdf",
        "description": "PDF document representing an invoice or receipt"
    }
    graph.add_type(DataType(name="PDFInvoice", schema_def=pdf_invoice_schema))
    print("    - Added Type: PDFInvoice")

    # Type 5: Knowledge Graph Triples (The Goal)
    kg_triples_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "predicate": {"type": "string"},
                "object": {"type": "string"}
            }
        }
    }
    graph.add_type(DataType(name="KGTriples", schema_def=kg_triples_schema))
    print("    - Added Type: KGTriples (Goal)")

    print("\n[2] Defined Ontology Types.")

    # 3. Define a Task and Run Gap Detection
    print("\n[3] Scenario: Extract Knowledge Graph from Consultant Profile (HTML)")
    
    start_type = "ConsultantProfile"
    target_type = "KGTriples"
    
    print(f"    - Start: {start_type}")
    print(f"    - Target: {target_type}")
    print("    - Running Gap Detector...")

    gap_result = graph.detect_gap(start_type, target_type)

    if gap_result["gap"]:
        print("\n[!] GAP DETECTED!")
        print(f"    Missing Edge: {gap_result['source']} -> {gap_result['target']}")
        
        # 4. Simulate Prompt Generation
        print("\n[4] Generating Synthesis Prompt (Simulation)...")
        
        prompt = f"""
You are an expert Python developer.
We have a data type '{start_type}' with schema:
{json.dumps(graph.graph.nodes[start_type]['schema'], indent=2)}

We need to transform it into '{target_type}' with schema:
{json.dumps(graph.graph.nodes[target_type]['schema'], indent=2)}

Write a Python function `transform(input_data) -> output_data` that performs this conversion.
Ensure the output strictly adheres to the target schema.
"""
        print("-" * 40)
        print(prompt)
        print("-" * 40)
        
        print("\n[Next Step] In a real system, this prompt would be sent to an LLM to synthesize the tool.")
    else:
        print("\n[OK] Path found! No synthesis needed.")

if __name__ == "__main__":
    main()
