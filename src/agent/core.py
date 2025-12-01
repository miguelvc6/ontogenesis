import json
import os
from typing import Any, Dict, List, Optional

from ontology.graph import CapabilityGraph
from ontology.types import DataType
from ontology.tools import Tool
from synthesis.factory import LLMFactory
from execution.runner import CodeRunner
from execution.docker_runner import DockerRunner
from utils.code_parsing import extract_code_block
from utils.tracer import tracer
from synthesis.test_generator import TestGenerator

class OntoGenesisAgent:
    def __init__(self, llm_provider: str = "openai", model: Optional[str] = None, execution_mode: str = "local"):
        self.graph = CapabilityGraph()
        self.llm_provider = LLMFactory.create_provider(llm_provider, model=model)
        self.test_generator = TestGenerator()
        
        if execution_mode == "docker":
            self.runner = DockerRunner()
        else:
            self.runner = CodeRunner()
            
        tracer.log_event("agent_init", {"llm_provider": llm_provider, "model": model, "execution_mode": execution_mode})

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

    def solve_task(self, start_type: str, target_type: str, input_data: Any, verification_fn: Optional[callable] = None, max_retries: int = 3) -> Any:
        """
        Attempts to transform input_data (of start_type) to target_type.
        Includes a feedback loop for self-correction.
        """
        tracer.start_span("solve_task", {"start_type": start_type, "target_type": target_type})
        
        # 1. Gap Detection
        gap_result = self.graph.detect_gap(start_type, target_type)
        
        if not gap_result["gap"]:
            tracer.end_span(outputs="Path exists (not implemented)")
            raise NotImplementedError("Multi-step execution not yet implemented.")
            
        # 2. Synthesis Loop
        print(f"[Agent] Gap detected: {start_type} -> {target_type}. Synthesizing tool...")
        
        current_code = None
        feedback = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"[Agent] Attempt {attempt}/{max_retries}. Retrying with feedback...")
                
                # Generate Code (with optional feedback)
                current_code = self._synthesize_tool(start_type, target_type, feedback=feedback, previous_code=current_code)
                
                # Execute
                print("[Agent] Executing synthesized tool...")
                result = self._execute_tool(current_code, input_data)
                
                # Verify
                if verification_fn:
                    print("[Agent] Verifying result (User Provided)...")
                    verification_fn(result) # Should raise exception on failure
                elif isinstance(self.runner, DockerRunner):
                    print("[Agent] Verifying result (Schema-Based)...")
                    target_schema = self.graph.graph.nodes[target_type]['schema']
                    test_code = self.test_generator.generate_test_code(target_type, target_schema)
                    self.runner.verify_result(result, test_code)
                
                # Success!
                tracer.end_span(outputs="Task completed")
                return result
                
            except Exception as e:
                print(f"[Agent] Attempt {attempt} failed: {e}")
                feedback = str(e)
                tracer.log_event("attempt_failed", {"attempt": attempt, "error": feedback})
                
                if attempt == max_retries:
                    tracer.end_span(error=f"Max retries reached. Last error: {feedback}")
                    raise RuntimeError(f"Failed to solve task after {max_retries} retries. Last error: {feedback}")

    def _synthesize_tool(self, start_type: str, target_type: str, feedback: Optional[str] = None, previous_code: Optional[str] = None) -> str:
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
        if feedback and previous_code:
            prompt += f"""
\nPREVIOUS ATTEMPT FAILED.
CODE:
{previous_code}

ERROR:
{feedback}

Fix the code to resolve the error.
"""
        response = self.llm_provider.generate(prompt)
        return extract_code_block(response)

    def _execute_tool(self, code: str, input_data: Any) -> Any:
        """Executes the generated code."""
        # We assume the entry point is always 'transform' for now
        return self.runner.run_code(code, "transform", input_data=input_data)
