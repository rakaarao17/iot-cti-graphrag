"""Local text embeddings using sentence-transformers (no API key required)."""

from functools import lru_cache
from typing import List

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def get_local_embeddings(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Encode texts into 384-dim vectors using all-MiniLM-L6-v2.

    Model is cached after first load. Works fully offline after first download.
    First call downloads ~90MB model to ~/.cache/huggingface/hub/.
    """
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return [v.tolist() for v in vectors]
