from src.services.graph_embeddings.text_embeddings import (
    get_local_embeddings, EMBEDDING_DIM
)


def test_get_local_embeddings_returns_correct_shape():
    texts = ["IoT device Mirai botnet attack", "Benign network flow"]
    result = get_local_embeddings(texts)
    assert len(result) == 2
    assert len(result[0]) == EMBEDDING_DIM
    assert len(result[1]) == EMBEDDING_DIM


def test_get_local_embeddings_similar_texts_close_in_space():
    import numpy as np
    texts = ["DDoS attack flood", "Distributed denial of service flood"]
    unrelated = ["The weather is nice today"]
    embs = get_local_embeddings(texts + unrelated)

    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_related = cosine(embs[0], embs[1])
    sim_unrelated = cosine(embs[0], embs[2])
    assert sim_related > sim_unrelated, "Semantically similar texts should be closer"


def test_get_local_embeddings_empty_list():
    result = get_local_embeddings([])
    assert result == []


def test_get_local_embeddings_single_text():
    result = get_local_embeddings(["test"])
    assert len(result) == 1
    assert len(result[0]) == EMBEDDING_DIM
