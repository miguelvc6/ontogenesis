from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generates text based on the prompt.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system instruction.
            **kwargs: Additional provider-specific arguments (e.g., temperature).
            
        Returns:
            The generated text.
        """
        pass
