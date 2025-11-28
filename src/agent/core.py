import json
import os
from typing import Any, Dict, List, Optional

from ontology.graph import CapabilityGraph
from ontology.types import DataType
from ontology.tools import Tool
from synthesis.factory import LLMFactory
from execution.runner import CodeRunner
from utils.code_parsing import extract_code_block
from utils.tracer import tracer

class OntoGenesisAgent:
    def __init__(self, llm_provider: str = "openai", model: Optional[str] = None):
        self.graph = CapabilityGraph()
        self.llm_provider = LLMFactory.create_provider(llm_provider, model=model)
        self.runner = CodeRunner()
        tracer.log_event("agent_init", {"llm_provider": llm_provider, "model": model})

    def register_type(self, name: str, schema: Dict[str, Any]):
        """Registers a new data type in the ontology."""
        self.graph.add_type(DataType(name=name, schema_def=schema))

    def register_tool(self, tool: Tool):
        """Registers a new tool in the ontology."""
        self.graph.add_tool(tool)

    def save_ontology(self, path: str):
        """Saves the current ontology to a file."""
        self.graph.save_to_json(path)

    def load_ontology(self, path: str):
        """Loads the ontology from a file."""
        self.graph.load_from_json(path)

    def solve_task(self, start_type: str, target_type: str, input_data: Any) -> Any:
        """
        Attempts to transform input_data (of start_type) to target_type.
        If a path exists, it executes it.
        If not, it attempts to synthesize a tool.
        """
        tracer.start_span("solve_task", {"start_type": start_type, "target_type": target_type})
        
        # 1. Gap Detection
        gap_result = self.graph.detect_gap(start_type, target_type)
        
        if not gap_result["gap"]:
            # Path exists (TODO: Implement multi-step execution)
            # For v0/v1, we assume direct edges or 1-step synthesis
            tracer.end_span(outputs="Path exists (not implemented)")
            raise NotImplementedError("Multi-step execution not yet implemented.")
            
        # 2. Synthesis
        print(f"[Agent] Gap detected: {start_type} -> {target_type}. Synthesizing tool...")
        code = self._synthesize_tool(start_type, target_type)
        
        # 3. Execution
        print("[Agent] Executing synthesized tool...")
        result = self._execute_tool(code, input_data)
        
        tracer.end_span(outputs="Task completed")
        return result

    def _synthesize_tool(self, start_type: str, target_type: str) -> str:
        """Generates code to transform start_type to target_type."""
        start_schema = self.graph.graph.nodes[start_type]['schema']
        target_schema = self.graph.graph.nodes[target_type]['schema']
        
        prompt = f"""
You are an expert Python developer.
We have a data type '{start_type}' with schema:
{json.dumps(start_schema, indent=2)}

We need to transform it into '{target_type}' with schema:
{json.dumps(target_schema, indent=2)}

Write a Python function `transform(input_data) -> output_data` that performs this conversion.
The input is of type {start_type}.
The output must strictly adhere to the target schema.
If the input is HTML, use BeautifulSoup.
Use specific predicates if the target schema implies a Knowledge Graph (e.g., hasName, hasRole).
Return ONLY the python code, wrapped in a markdown code block.
"""
        response = self.llm_provider.generate(prompt)
        return extract_code_block(response)

    def _execute_tool(self, code: str, input_data: Any) -> Any:
        """Executes the generated code."""
        # We assume the entry point is always 'transform' for now
        return self.runner.run_code(code, "transform", input_data=input_data)
