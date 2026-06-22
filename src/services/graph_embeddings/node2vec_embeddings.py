"""
Node2Vec structural embeddings for the device communication graph.

Uses random-walk-based node2vec (Grover & Leskovec, SIGKDD 2016).
Parameters follow the paper's recommendation for homophily (p=1, q=0.5).
"""

from typing import Dict, List, Tuple

NODE2VEC_DIM = 128
WALK_LENGTH = 30
NUM_WALKS = 200
WINDOW = 10
MIN_COUNT = 1
P = 1.0   # return parameter (controls DFS vs BFS balance)
Q = 0.5   # in-out parameter (< 1 biases toward BFS / community structure)
WORKERS = 4
EPOCHS = 1


def compute_node2vec(
    edges: List[Tuple[str, str, int]],
    dimensions: int = NODE2VEC_DIM,
    walk_length: int = WALK_LENGTH,
    num_walks: int = NUM_WALKS,
    p: float = P,
    q: float = Q,
) -> Dict[str, List[float]]:
    """
    Compute node2vec embeddings from a weighted edge list.

    Args:
        edges: List of (source, target, weight) tuples
        dimensions: Embedding dimension
        walk_length: Length of each random walk
        num_walks: Number of walks per node
        p: Return parameter
        q: In-out parameter

    Returns:
        Dict mapping node_id -> embedding vector (List[float])
    """
    if not edges:
        return {}

    try:
        import networkx as nx
        from node2vec import Node2Vec
    except ImportError:
        raise ImportError("Install node2vec: pip install node2vec")

    G = nx.DiGraph()
    for src, dst, weight in edges:
        G.add_edge(src, dst, weight=float(weight))

    if G.number_of_nodes() < 2:
        return {}

    n2v = Node2Vec(
        G,
        dimensions=dimensions,
        walk_length=walk_length,
        num_walks=num_walks,
        p=p,
        q=q,
        workers=WORKERS,
        quiet=True,
    )
    model = n2v.fit(window=WINDOW, min_count=MIN_COUNT, epochs=EPOCHS)

    return {
        node: model.wv[node].tolist()
        for node in G.nodes()
        if node in model.wv
    }
