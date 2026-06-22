"""Ablation study: compares three retrieval conditions for the GraphRAG component."""

import time
from enum import Enum
from typing import Any, Dict, List

from src.services.graphrag.retrievers import CypherRetriever, VectorGraphRetriever


class AblationCondition(Enum):
    CYPHER_ONLY = "cypher_only"
    VECTOR_ONLY = "vector_only"
    COMBINED = "combined"


def run_ablation_condition(
    query: Dict[str, Any],
    condition: AblationCondition,
    search_type: str = "attack",
) -> Dict[str, Any]:
    """
    Run a single query under one retrieval condition.

    Returns a result dict with context_text, raw results, and latency.
    """
    cypher = CypherRetriever()
    vector = VectorGraphRetriever()

    start = time.perf_counter()

    if condition == AblationCondition.CYPHER_ONLY:
        raw = cypher.retrieve(query["query"])
    elif condition == AblationCondition.VECTOR_ONLY:
        raw = vector.retrieve(query["query"], search_type=search_type)
    else:  # COMBINED
        cypher_raw = cypher.retrieve(query["query"])
        vector_raw = vector.retrieve(query["query"], search_type=search_type)
        combined_text = (
            cypher_raw.get("context_text", "") + "\n\n" + vector_raw.get("context_text", "")
        )
        raw = {
            "context_text": combined_text,
            "results": cypher_raw.get("results", []) + vector_raw.get("results", []),
        }

    latency_ms = (time.perf_counter() - start) * 1000

    return {
        "query_id": query["id"],
        "query": query["query"],
        "condition": condition.value,
        "context_text": raw.get("context_text", ""),
        "results": raw.get("results", []),
        "latency_ms": round(latency_ms, 2),
    }


def run_full_ablation(
    queries: List[Dict],
    output_path: str = "data/eval/ablation_results.json",
) -> List[Dict]:
    """
    Run all queries under all three conditions. Save results to JSON.

    Must be called after Neo4j is populated with train data.
    """
    import json
    from pathlib import Path

    all_results = []
    for query in queries:
        for condition in AblationCondition:
            result = run_ablation_condition(query, condition)
            all_results.append(result)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)

    return all_results
