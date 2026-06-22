"""
Stage 6: Ollama LLM Client v2.

Extends ollama_client with get_model_name() and a get_adapter() factory.
Import OllamaClient and get_adapter from here for all new code.
"""

from src.services.threat_explanation.ollama_client import OllamaClient as _BaseClient


class OllamaClient(_BaseClient):
    """OllamaClient v2 -- adds get_model_name() for adapter compatibility."""

    def get_model_name(self) -> str:
        return self.model


def get_adapter(model: str = None, **kwargs) -> OllamaClient:
    """Return a configured OllamaClient for the given model."""
    return OllamaClient(model=model, **kwargs)
