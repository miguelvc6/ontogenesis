import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from agent.core import OntoGenesisAgent
from ontology.tools import Tool

@patch("agent.core.LLMFactory")
@patch("agent.core.CodeRunner")
def test_agent_solve_task_synthesis(mock_runner_class, mock_factory):
    # Setup Mocks
    mock_llm = MagicMock()
    mock_factory.create_provider.return_value = mock_llm
    mock_llm.generate.return_value = "```python\ndef transform(data):\n    return 'processed'\n```"
    
    mock_runner = MagicMock()
    mock_runner_class.return_value = mock_runner
    mock_runner.run_code.return_value = "processed"

    # Initialize Agent
    agent = OntoGenesisAgent()
    
    # Register Types
    agent.register_type("TypeA", {"type": "string"})
    agent.register_type("TypeB", {"type": "string"})
    
    # Solve Task (Gap exists)
    result = agent.solve_task("TypeA", "TypeB", "input")
    
    # Verify
    assert result == "processed"
    mock_llm.generate.assert_called_once()
    mock_runner.run_code.assert_called_once()

@patch("agent.core.LLMFactory")
def test_agent_solve_task_no_gap(mock_factory):
    # Setup Mocks
    mock_llm = MagicMock()
    mock_factory.create_provider.return_value = mock_llm
    
    agent = OntoGenesisAgent()
    agent.register_type("TypeA", {"type": "string"})
    agent.register_type("TypeB", {"type": "string"})
    
    # Add tool to bridge gap
    tool = Tool(name="tool_a_to_b", input_type="TypeA", output_type="TypeB")
    agent.register_tool(tool)
    
    # Solve Task (No gap)
    # Currently raises NotImplementedError as per implementation
    with pytest.raises(NotImplementedError):
        agent.solve_task("TypeA", "TypeB", "input")
