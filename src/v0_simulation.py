import sys
import os
import json
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.ontology.graph import CapabilityGraph
from src.ontology.types import DataType
from src.synthesis.factory import LLMFactory
from src.utils.code_parsing import extract_code_block

def main():
    load_dotenv()
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
        
        # 4. Generate Prompt
        print("\n[4] Generating Synthesis Prompt...")
        
        prompt = f"""
You are an expert Python developer.
We have a data type '{start_type}' with schema:
{json.dumps(graph.graph.nodes[start_type]['schema'], indent=2)}

We need to transform it into '{target_type}' with schema:
{json.dumps(graph.graph.nodes[target_type]['schema'], indent=2)}

Write a Python function `transform(input_data: str) -> List[Dict[str, str]]` that performs this conversion.
The input is the raw HTML string.
The output must be a list of dictionaries, each with 'subject', 'predicate', 'object' keys.
Use BeautifulSoup to parse the HTML.
Ensure the output strictly adheres to the target schema.
Return ONLY the python code, wrapped in a markdown code block.
"""
        print("-" * 40)
        print(prompt)
        print("-" * 40)
        
        # 5. Call LLM
        print("\n[5] Calling LLM (OpenAI)...")
        try:
            provider = LLMFactory.create_provider("openai")
            response = provider.generate(prompt)
            
            print("\n[6] Received Response from LLM.")
            code = extract_code_block(response)
            
            print("\n[7] Extracted Code:")
            print("-" * 40)
            print(code)
            print("-" * 40)
            
            # Save code to file for inspection
            output_file = "generated_tool.py"
            with open(output_file, "w") as f:
                f.write(code)
            print(f"\n[8] Saved code to {output_file}")

            # 6. Execute Code
            print("\n[9] Executing Generated Code...")
            from src.execution.runner import CodeRunner
            
            # Load sample data
            sample_file = os.path.join(os.path.dirname(__file__), "..", "data", "consultant_profile_mark.html")
            with open(sample_file, "r", encoding="utf-8") as f:
                input_data = f.read()
            
            runner = CodeRunner()
            try:
                # We assume the entry point is 'transform' as requested in the prompt
                result = runner.run_code(code, "transform", input_data=input_data)
                
                print("\n[10] Execution Result (Knowledge Graph Triples):")
                print("-" * 40)
                print(json.dumps(result, indent=2))
                print("-" * 40)
                
                # Basic Verification
                print("\n[11] Verifying Result...")
                expected_name = "Markus Weber"
                found_name = any(t['object'] == expected_name for t in result if t['predicate'] == 'hasName')
                
                if found_name:
                    print(f"    [PASS] Found expected name: {expected_name}")
                else:
                    print(f"    [FAIL] Did not find name: {expected_name}")
                    
            except Exception as e:
                print(f"\n[ERROR] Execution failed: {e}")
                
        except Exception as e:
            print(f"\n[ERROR] LLM Generation failed: {e}")

    else:
        print("\n[OK] Path found! No synthesis needed.")

if __name__ == "__main__":
    main()
