"""
Embedding Adapter Implementation

Concrete implementation of EmbeddingPort for local sentence-transformers.
Provides deterministic mock embeddings for testing.
"""

import sys
from pathlib import Path
from typing import List

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.ports.embedding_port import EmbeddingPort


class MockEmbeddingAdapter(EmbeddingPort):
    """
    Mock embedding adapter for testing without API access.

    Returns deterministic random embeddings for reproducibility.
    """

    def __init__(self, embedding_dimension: int = 384, seed: int = 42):
        """
        Initialize mock embedding adapter.

        Args:
            embedding_dimension: Output embedding dimension
            seed: Random seed for reproducibility
        """
        self.embedding_dimension = embedding_dimension
        self.seed = seed
        self.request_count = 0

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text (mock)."""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts (mock with deterministic output)."""
        if not texts:
            return []

        np.random.seed(self.seed)
        embeddings = [
            np.random.randn(self.embedding_dimension).tolist()
            for _ in texts
        ]
        self.request_count += 1
        return embeddings

    def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self.embedding_dimension

    def get_model_name(self) -> str:
        """Get model name (mock)."""
        return "mock-embeddings"

    def get_stats(self) -> dict:
        """Get stats."""
        return {
            "model": self.get_model_name(),
            "dimension": self.embedding_dimension,
            "requests": self.request_count,
        }
