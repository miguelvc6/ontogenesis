import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from synthesis.factory import LLMFactory
from synthesis.providers.openai_provider import OpenAIProvider
from synthesis.providers.ollama_provider import OllamaProvider

def test_factory_creates_openai():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        provider = LLMFactory.create_provider("openai")
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"

def test_factory_creates_ollama():
    provider = LLMFactory.create_provider("ollama")
    assert isinstance(provider, OllamaProvider)

def test_factory_raises_unknown():
    with pytest.raises(ValueError):
        LLMFactory.create_provider("unknown")

@patch("synthesis.providers.openai_provider.OpenAI")
def test_openai_generate(mock_openai_class):
    # Setup mock
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Generated Code"
    mock_client.chat.completions.create.return_value = mock_response

    provider = OpenAIProvider(api_key="test")
    result = provider.generate("prompt")
    
    assert result == "Generated Code"
    mock_client.chat.completions.create.assert_called_once()

@patch("synthesis.providers.ollama_provider.requests.post")
def test_ollama_generate(mock_post):
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Ollama Code"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    provider = OllamaProvider()
    result = provider.generate("prompt")
    
    assert result == "Ollama Code"
    mock_post.assert_called_once()

def test_openai_model_selection():
    # Test default
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
        provider = OpenAIProvider()
        assert provider.model == "gpt-4o"

    # Test env var
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-5-nano"}):
        provider = OpenAIProvider()
        assert provider.model == "gpt-5-nano"

    # Test explicit override
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-5-nano"}):
        provider = OpenAIProvider(model="gpt-5.1")
        assert provider.model == "gpt-5.1"
