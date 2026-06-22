"""
LLM model comparison runner.

Runs multiple LLM adapters against the same queries and collects
responses + grounding results for side-by-side comparison.
"""

from dataclasses import dataclass, field

from src.adapters.llm_adapters import LLMAdapter, LLMResponse
from src.services.threat_explanation.grounding import GroundingResult, check_grounding


@dataclass
class ModelComparisonResult:
    """Comparison result for a single query across all models."""
    query_id: str
    query: str
    context: str                           # retrieved context passed to all models
    responses: dict[str, LLMResponse]      # model_name -> LLMResponse
    grounding: dict[str, GroundingResult]  # model_name -> GroundingResult


def run_model_comparison(
    queries: list[dict],
    adapters: list[LLMAdapter],
) -> list[ModelComparisonResult]:
    """
    Run all adapters against each query+context pair.

    For each query:
      - Calls adapter.generate(query["query"], query["context"]) for every adapter.
      - If the adapter raises, captures the exception in LLMResponse.error.
      - Runs check_grounding on each response.

    Returns one ModelComparisonResult per query.
    """
    results: list[ModelComparisonResult] = []

    for i, query in enumerate(queries):
        print(f"[{i + 1}/{len(queries)}] {query.get('id') or query.get('query_id', 'unknown')}")

        responses: dict[str, LLMResponse] = {}
        grounding: dict[str, GroundingResult] = {}

        for adapter in adapters:
            model_name = adapter.model_name
            try:
                response = adapter.generate(query["query"], query["context"])
            except Exception as exc:
                # Capture error without crashing -- return a sentinel LLMResponse
                response = LLMResponse(
                    model_name=model_name,
                    deployment=getattr(adapter, "deployment", "unknown"),
                    prompt=query["query"],
                    context=query["context"],
                    response_text="",
                    latency_ms=0.0,
                    input_tokens=0,
                    output_tokens=0,
                    error=str(exc),
                )

            responses[model_name] = response

            # Grounding is best-effort; empty response -> default GroundingResult
            grounding[model_name] = check_grounding(
                response.response_text, query["context"]
            )

        results.append(ModelComparisonResult(
            query_id=query.get("id") or query.get("query_id", "unknown"),
            query=query["query"],
            context=query["context"],
            responses=responses,
            grounding=grounding,
        ))

    return results
