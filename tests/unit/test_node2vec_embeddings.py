import pytest
from src.services.graph_embeddings.node2vec_embeddings import (
    compute_node2vec, NODE2VEC_DIM
)


def test_compute_node2vec_returns_embeddings_for_all_nodes():
    edges = [
        ("192.168.1.1", "10.0.0.1", 5),
        ("192.168.1.1", "10.0.0.2", 3),
        ("192.168.1.2", "10.0.0.1", 8),
        ("10.0.0.1", "192.168.1.3", 2),
    ]
    result = compute_node2vec(edges)
    unique_nodes = {"192.168.1.1", "10.0.0.1", "192.168.1.2", "192.168.1.3", "10.0.0.2"}
    assert set(result.keys()) == unique_nodes


def test_compute_node2vec_embedding_dimension():
    edges = [("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]
    result = compute_node2vec(edges)
    assert all(len(v) == NODE2VEC_DIM for v in result.values())


def test_compute_node2vec_returns_empty_for_no_edges():
    result = compute_node2vec([])
    assert result == {}


def test_compute_node2vec_single_edge():
    edges = [("A", "B", 1)]
    result = compute_node2vec(edges)
    assert "A" in result and "B" in result
