"""
Unit tests for generate_comparison_report().

TDD: tests written before implementation.
"""

from __future__ import annotations

from typing import List

import pytest

from src.adapters.llm_adapters import LLMResponse
from src.services.evaluation.llm_comparison import ModelComparisonResult
from src.services.evaluation.comparison_report import generate_comparison_report
from src.services.threat_explanation.grounding import GroundingResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(
    model_name: str,
    deployment: str = "local",
    latency_ms: float = 100.0,
    output_tokens: int = 50,
    response_text: str = "Some IoT attack response.",
    error: str | None = None,
) -> LLMResponse:
    return LLMResponse(
        model_name=model_name,
        deployment=deployment,
        prompt="Test prompt",
        context="Test context",
        response_text=response_text,
        latency_ms=latency_ms,
        input_tokens=10,
        output_tokens=output_tokens,
        error=error,
    )


def _make_grounding(ratio: float = 0.8) -> GroundingResult:
    return GroundingResult(
        grounded_claims=4,
        ungrounded_claims=1,
        grounding_ratio=ratio,
        ungrounded_entities=[],
    )


def make_results(n: int = 3) -> List[ModelComparisonResult]:
    """Helper: creates n synthetic ModelComparisonResult objects."""
    results = []
    models = ["phi3:latest", "gemma4:e2b"]
    for i in range(n):
        query_id = f"te-{i + 1:02d}"
        responses = {m: _make_response(m, latency_ms=100.0 + i * 10) for m in models}
        grounding = {m: _make_grounding(ratio=0.8) for m in models}
        results.append(ModelComparisonResult(
            query_id=query_id,
            query=f"Query {i + 1}",
            context="Network flows context",
            responses=responses,
            grounding=grounding,
        ))
    return results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_generate_comparison_report_structure(tmp_path):
    """Report dict has 'models' and 'per_query' keys; per_query length matches results."""
    results = make_results(3)
    report = generate_comparison_report(results, str(tmp_path))
    assert "models" in report
    assert "per_query" in report
    assert len(report["per_query"]) == 3


def test_generate_comparison_report_files_created(tmp_path):
    """Both JSON and Markdown report files are written to output_dir."""
    results = make_results(2)
    generate_comparison_report(results, str(tmp_path))
    assert (tmp_path / "comparison_report.json").exists()
    assert (tmp_path / "comparison_report.md").exists()


def test_generate_comparison_report_aggregates_correctly(tmp_path):
    """Two results for the same model with latencies 100ms and 200ms → mean=150.0."""
    models = ["phi3:latest"]
    results = [
        ModelComparisonResult(
            query_id="te-01",
            query="Query 1",
            context="ctx",
            responses={"phi3:latest": _make_response("phi3:latest", latency_ms=100.0, output_tokens=40)},
            grounding={"phi3:latest": _make_grounding(ratio=0.6)},
        ),
        ModelComparisonResult(
            query_id="te-02",
            query="Query 2",
            context="ctx",
            responses={"phi3:latest": _make_response("phi3:latest", latency_ms=200.0, output_tokens=60)},
            grounding={"phi3:latest": _make_grounding(ratio=1.0)},
        ),
    ]
    report = generate_comparison_report(results, str(tmp_path))
    phi_stats = report["models"]["phi3:latest"]
    assert phi_stats["mean_latency_ms"] == pytest.approx(150.0)
    assert phi_stats["median_latency_ms"] == pytest.approx(150.0)
    assert phi_stats["mean_grounding_ratio"] == pytest.approx(0.8)
    assert phi_stats["mean_output_tokens"] == pytest.approx(50.0)
    assert phi_stats["error_rate"] == pytest.approx(0.0)


def test_generate_comparison_report_empty(tmp_path):
    """Empty results list → query_count=0, models={}, files still written."""
    report = generate_comparison_report([], str(tmp_path))
    assert report["query_count"] == 0
    assert report["models"] == {}
    assert (tmp_path / "comparison_report.json").exists()
    assert (tmp_path / "comparison_report.md").exists()
