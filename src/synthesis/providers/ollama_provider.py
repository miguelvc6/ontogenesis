import os
import requests
from typing import Optional
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    """Concrete implementation for Ollama (local models)."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        url = f"{self.base_url}/api/generate"
        
        # Ollama API expects a single prompt or a conversation. 
        # For simplicity in this v0, we'll combine system and user prompt if needed, 
        # or use the 'system' parameter if the API supports it (it does).
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to communicate with Ollama at {self.base_url}: {e}")
