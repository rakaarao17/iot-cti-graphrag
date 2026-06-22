"""
Stage 5: Neo4j Vector Store Management.

Creates and manages vector indexes in Neo4j for embedding-based retrieval.
Provides utilities to insert, query, and verify vector indexes.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import EMBEDDING_DIMENSION, TOP_K_RESULTS, logger
from src.services.knowledge_graph.neo4j_connection import (
    run_query, run_write_query, verify_connectivity
)


# "" Vector Index Names """"""""""""""""""""""""""""""""""""""""""""""""""""""

VECTOR_INDEXES = {
    "device_embedding": {
        "label": "Device",
        "property": "embedding",
        "dimension": EMBEDDING_DIMENSION,
    },
    "attack_embedding": {
        "label": "AttackType",
        "property": "embedding",
        "dimension": EMBEDDING_DIMENSION,
    },
    "mitre_embedding": {
        "label": "MITRETechnique",
        "property": "embedding",
        "dimension": EMBEDDING_DIMENSION,
    },
}


def verify_vector_indexes() -> Dict[str, bool]:
    """Verify that all vector indexes exist and are operational."""
    results = {}

    try:
        indexes = run_query("SHOW INDEXES WHERE type = 'VECTOR'")
        existing = {idx.get("name", ""): idx for idx in indexes}

        for name, config in VECTOR_INDEXES.items():
            if name in existing:
                idx = existing[name]
                state = idx.get("state", "UNKNOWN")
                results[name] = state == "ONLINE"
                logger.info(f"  {'[OK]' if results[name] else '[FAIL]'} {name}: {state}")
            else:
                results[name] = False
                logger.warning(f"  [FAIL] {name}: NOT FOUND")

    except Exception as e:
        logger.error(f"Failed to check vector indexes: {e}")
        for name in VECTOR_INDEXES:
            results[name] = False

    return results


def vector_search(
    query_embedding: List[float],
    index_name: str = "device_embedding",
    top_k: int = None,
) -> List[Dict]:
    """
    Perform a vector similarity search using a Neo4j vector index.

    Args:
        query_embedding: The query embedding vector
        index_name: Name of the vector index to search
        top_k: Number of results to return

    Returns:
        List of matching nodes with similarity scores
    """
    top_k = top_k or TOP_K_RESULTS
    config = VECTOR_INDEXES.get(index_name)

    if not config:
        logger.error(f"Unknown vector index: {index_name}")
        return []

    label = config["label"]

    query = f"""
    CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
    YIELD node, score
    RETURN node, score
    ORDER BY score DESC
    """

    try:
        results = run_query(query, {
            "index_name": index_name,
            "top_k": top_k,
            "query_embedding": query_embedding,
        })

        formatted = []
        for r in results:
            node = r["node"]
            formatted.append({
                "score": r["score"],
                **{k: v for k, v in node.items() if k != "embedding" and k != "structural_embedding"},
            })

        return formatted

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


def vector_search_with_traversal(
    query_embedding: List[float],
    index_name: str = "device_embedding",
    top_k: int = 5,
    traversal_depth: int = 2,
) -> List[Dict]:
    """
    Vector search + graph traversal for richer context retrieval.

    Finds semantically similar nodes, then traverses their graph neighborhood
    to gather related context (attacks, MITRE techniques, peers).
    """
    config = VECTOR_INDEXES.get(index_name)
    if not config:
        return []

    label = config["label"]

    if label == "Device":
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
        YIELD node AS device, score
        OPTIONAL MATCH (device)-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
        WHERE a.name <> 'Benign'
        WITH device, score,
             collect(DISTINCT a.name) as attacks,
             count(DISTINCT f) as malicious_flows
        OPTIONAL MATCH (a2:AttackType)<-[:CLASSIFIED_AS]-(f2:Flow)<-[:INITIATES]-(device)
        OPTIONAL MATCH (a2)-[:MAPS_TO]->(m:MITRETechnique)
        WITH device, score, attacks, malicious_flows,
             collect(DISTINCT m.technique_id) as mitre_ids,
             collect(DISTINCT m.name) as mitre_names
        OPTIONAL MATCH (device)-[comm:COMMUNICATES_WITH]->(peer:Device)
        WITH device, score, attacks, malicious_flows, mitre_ids, mitre_names,
             collect(DISTINCT peer.ip)[..5] as top_peers
        RETURN device.ip as ip,
               device.role as role,
               device.dataset as dataset,
               device.malicious_ratio as malicious_ratio,
               device.text_description as description,
               score,
               attacks,
               malicious_flows,
               mitre_ids,
               mitre_names,
               top_peers
        ORDER BY score DESC
        """
    elif label == "AttackType":
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
        YIELD node AS attack, score
        OPTIONAL MATCH (attack)-[:BELONGS_TO]->(c:AttackCategory)
        OPTIONAL MATCH (attack)-[:MAPS_TO]->(m:MITRETechnique)
        OPTIONAL MATCH (f:Flow)-[:CLASSIFIED_AS]->(attack)
        WITH attack, score, c, m, count(f) as flow_count
        RETURN attack.name as name,
               attack.description as description,
               c.name as category,
               c.severity as severity,
               m.technique_id as mitre_id,
               m.name as mitre_technique,
               m.tactic as mitre_tactic,
               flow_count,
               score
        ORDER BY score DESC
        """
    else:
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        """

    try:
        return run_query(query, {
            "index_name": index_name,
            "top_k": top_k,
            "query_embedding": query_embedding,
        })
    except Exception as e:
        logger.error(f"Vector search with traversal failed: {e}")
        return []


def get_embedding_stats() -> Dict:
    """Get statistics about embeddings stored in the database."""
    stats = {}

    for index_name, config in VECTOR_INDEXES.items():
        label = config["label"]
        prop = config["property"]
        result = run_query(f"""
            MATCH (n:{label})
            WHERE n.{prop} IS NOT NULL
            RETURN count(n) as embedded,
                   size(n.{prop}) as dim
            LIMIT 1
        """)
        if result:
            stats[index_name] = {
                "embedded_nodes": result[0]["embedded"],
                "dimension": result[0].get("dim", 0),
            }

    return stats


if __name__ == "__main__":
    if verify_connectivity():
        print("\nVector Index Status:")
        verify_vector_indexes()

        print("\nEmbedding Stats:")
        stats = get_embedding_stats()
        for name, info in stats.items():
            print(f"  {name}: {info['embedded_nodes']} nodes, dim={info.get('dimension', '?')}")
