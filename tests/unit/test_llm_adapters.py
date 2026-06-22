"""
Tests for unified LLM adapter interface.
TDD: tests written before implementation.
No real API calls — all external I/O is mocked.
"""
from unittest.mock import patch

from src.adapters.llm_adapters import LLMAdapter, LLMResponse, OllamaAdapter


def test_ollama_adapter_returns_llm_response():
    with patch("src.adapters.llm_adapters.requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"response": "test answer"}
        mock_post.return_value.raise_for_status = lambda: None
        adapter = OllamaAdapter("phi3:latest")
        result = adapter.generate("What is this attack?", "Flow: 192.168.1.1")
    assert isinstance(result, LLMResponse)
    assert result.model_name == "phi3:latest"
    assert result.deployment == "local"
    assert result.response_text == "test answer"
    assert result.latency_ms >= 0
    assert result.error is None


def test_ollama_adapter_captures_error():
    with patch("src.adapters.llm_adapters.requests.post", side_effect=ConnectionError("refused")):
        adapter = OllamaAdapter("gemma4:e2b")
        result = adapter.generate("test", "ctx")
    assert result.response_text == ""
    assert "refused" in result.error



def test_llm_response_protocol():
    adapter = OllamaAdapter("phi3:latest")
    assert isinstance(adapter, LLMAdapter)
