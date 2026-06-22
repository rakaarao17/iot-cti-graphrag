"""Retrieval quality metrics: MRR and Hit@K."""

from typing import List, Set


def compute_mrr(ranked_results: List[str], relevant_ids: Set[str]) -> float:
    """Mean Reciprocal Rank for a single query."""
    for rank, doc_id in enumerate(ranked_results, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def compute_hit_at_k(ranked_results: List[str], relevant_ids: Set[str], k: int = 5) -> int:
    """Hit@K: 1 if any relevant document appears in top-k results, else 0."""
    return int(any(doc in relevant_ids for doc in ranked_results[:k]))


def compute_mean_mrr(all_query_results: List[dict]) -> float:
    """
    Compute mean MRR across a list of query results.

    Each dict in all_query_results must have:
    - "ranked_ids": List[str] -- retrieved document IDs in rank order
    - "relevant_ids": Set[str] -- ground-truth relevant IDs for this query
    """
    if not all_query_results:
        return 0.0
    scores = [
        compute_mrr(q["ranked_ids"], q["relevant_ids"])
        for q in all_query_results
    ]
    return round(sum(scores) / len(scores), 4)
