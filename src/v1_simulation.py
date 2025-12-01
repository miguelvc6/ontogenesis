import sys
import os
import json
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agent.core import OntoGenesisAgent
from src.utils.tracer import tracer

def main():
    load_dotenv()
    tracer.start_trace()
    print("=== OntoGenesis v1: Closed-Loop System (Simulation) ===\n")

    # 1. Initialize Agent
    agent = OntoGenesisAgent(llm_provider="openai", execution_mode="docker")
    print("[1] Initialized OntoGenesisAgent (Docker Mode).")

    # 2. Register Types
    # Type 1: Consultant Profile (HTML)
    consultant_profile_schema = {
        "type": "string",
        "format": "html",
        "description": "HTML page containing consultant profile with name, role, contact info, etc."
    }
    agent.register_type("ConsultantProfile", consultant_profile_schema)
    print("    - Registered Type: ConsultantProfile")

    # Type 2: Knowledge Graph Triples (The Goal)
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
    agent.register_type("KGTriples", kg_triples_schema)
    print("    - Registered Type: KGTriples")

    # 3. Load Input Data
    sample_file = os.path.join(os.path.dirname(__file__), "..", "data", "consultant_profile_mark.html")
    with open(sample_file, "r", encoding="utf-8") as f:
        input_data = f.read()
    print(f"\n[2] Loaded input data from {sample_file}")

    # 4. Solve Task
    print("\n[3] Agent solving task: ConsultantProfile -> KGTriples")
    
    def verify_result(result):
        expected_name = "Markus Weber"
        found_name = any(t['object'] == expected_name for t in result if t['predicate'] == 'hasName')
        if not found_name:
            raise ValueError(f"Did not find exact name: '{expected_name}'")
        print(f"    [PASS] Verification successful: Found '{expected_name}'")

    try:
        result = agent.solve_task("ConsultantProfile", "KGTriples", input_data, verification_fn=verify_result)
        
        print("\n[4] Task Result:")
        print("-" * 40)
        print(json.dumps(result, indent=2))
        print("-" * 40)
            
    except Exception as e:
        print(f"\n[ERROR] Agent failed: {e}")

if __name__ == "__main__":
    main()
