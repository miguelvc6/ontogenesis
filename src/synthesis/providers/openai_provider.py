import os
from typing import Optional
from openai import OpenAI
from .base import LLMProvider
from utils.tracer import tracer

class OpenAIProvider(LLMProvider):
    """Concrete implementation for OpenAI API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env var or pass it in.")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        tracer.start_span("llm_generate", {"provider": "openai", "model": self.model, "prompt_length": len(prompt)})
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            content = response.choices[0].message.content
            tracer.end_span(outputs={"response_length": len(content)})
            return content
        except Exception as e:
            tracer.end_span(error=str(e))
            raise e
