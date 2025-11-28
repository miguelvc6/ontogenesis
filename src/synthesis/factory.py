from typing import Optional
from .providers.base import LLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.ollama_provider import OllamaProvider

class LLMFactory:
    """Factory to create LLM providers."""

    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> LLMProvider:
        if provider_type.lower() == "openai":
            return OpenAIProvider(**kwargs)
        elif provider_type.lower() == "ollama":
            return OllamaProvider(**kwargs)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
