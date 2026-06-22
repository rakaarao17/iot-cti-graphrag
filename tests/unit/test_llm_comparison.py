"""
Unit tests for src/services/evaluation/llm_comparison.py

TDD: All tests written before implementation.
All tests are fully mocked — no real Ollama calls.
"""

from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock

import pytest

from src.services.evaluation.llm_comparison import (
    ModelComparisonResult,
    run_model_comparison,
)
from src.adapters.llm_adapters import LLMResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_adapter(name: str, deployment: str, response: str):
    """Return a minimal mock adapter that satisfies the LLMAdapter Protocol."""
    adapter = MagicMock()
    adapter.model_name = name
    adapter.deployment = deployment
    adapter.generate.return_value = LLMResponse(
        model_name=name,
        deployment=deployment,
        prompt="",
        context="",
        response_text=response,
        latency_ms=1.0,
        input_tokens=0,
        output_tokens=0,
        error=None,
    )
    return adapter


def make_error_adapter(name: str):
    """Return a mock adapter whose generate() raises an exception."""
    adapter = MagicMock()
    adapter.model_name = name
    adapter.deployment = "local"
    adapter.generate.side_effect = RuntimeError("connection refused")
    return adapter


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_run_model_comparison_returns_one_result_per_query():
    """run_model_comparison returns exactly one result per input query."""
    adapters = [
        make_mock_adapter("m1", "local", "answer1"),
        make_mock_adapter("m2", "cloud", "answer2"),
    ]
    queries = [
        {"id": "q1", "query": "What attack?", "context": "192.168.1.1 DDoS"},
        {"id": "q2", "query": "Which MITRE?", "context": "T1046 scan"},
    ]
    results = run_model_comparison(queries, adapters)

    assert len(results) == 2
    assert results[0].query_id == "q1"
    assert results[1].query_id == "q2"
    assert set(results[0].responses.keys()) == {"m1", "m2"}
    assert set(results[1].responses.keys()) == {"m1", "m2"}


def test_run_model_comparison_grounding_computed():
    """run_model_comparison populates grounding dict with GroundingResult for each model."""
    adapter = make_mock_adapter("m1", "local", "192.168.1.1 attacked via DDoS")
    queries = [{"id": "q1", "query": "test", "context": "192.168.1.1 DDoS"}]

    results = run_model_comparison(queries, [adapter])

    assert "m1" in results[0].grounding
    gr = results[0].grounding["m1"]
    assert gr.grounding_ratio >= 0.0
    # IP and DDoS are both in context → grounding_ratio should be 1.0
    assert gr.grounded_claims > 0


def test_run_model_comparison_captures_adapter_error():
    """When an adapter raises, the error is captured in LLMResponse.error — no crash."""
    error_adapter = make_error_adapter("error_model")
    queries = [{"id": "q1", "query": "What attack?", "context": "some context"}]

    results = run_model_comparison(queries, [error_adapter])

    assert len(results) == 1
    assert "error_model" in results[0].responses
    assert results[0].responses["error_model"].error is not None


def test_run_model_comparison_empty_queries():
    """run_model_comparison with no queries returns an empty list."""
    results = run_model_comparison([], [make_mock_adapter("m1", "local", "x")])
    assert results == []
