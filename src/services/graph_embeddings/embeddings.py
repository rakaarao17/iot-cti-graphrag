"""
Stage 4: Embeddings Generation.

Two types of embeddings:
1. Text Embeddings via sentence-transformers (all-MiniLM-L6-v2) - for semantic search in GraphRAG
2. Graph Structural Embeddings via Node2Vec - for topological similarity

Both are stored as node properties in Neo4j for retrieval.
"""

import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import logger
from src.services.knowledge_graph.neo4j_connection import (
    run_query, run_write_query, run_batch_query, verify_connectivity
)
from src.services.graph_embeddings.text_embeddings import get_local_embeddings
# Legacy alias -- kept for any callers that still reference the old name
get_gemini_embeddings = get_local_embeddings


# ==============================================================================
# Text Embeddings via sentence-transformers (local, no API key required)
# ==============================================================================

def generate_device_descriptions() -> List[Dict]:
    """
    Generate text descriptions for Device nodes for embedding.

    Creates a natural language description of each device's behavior
    that captures its role, traffic patterns, and threat profile.
    """
    query = """
    MATCH (d:Device)
    WHERE d.total_degree IS NOT NULL
    OPTIONAL MATCH (d)-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
    WITH d,
         collect(DISTINCT a.name) as attacks,
         count(DISTINCT f) as flow_count
    RETURN d.ip as ip,
           d.role as role,
           d.dataset as dataset,
           coalesce(d.malicious_ratio, 0.0) as mal_ratio,
           coalesce(d.total_degree, 0) as degree,
           coalesce(d.peer_count, 0) as peers,
           coalesce(d.port_diversity, 0) as ports,
           attacks,
           flow_count
    """
    devices = run_query(query)

    descriptions = []
    for d in devices:
        attacks = d.get("attacks", [])
        attack_str = ", ".join(attacks[:5]) if attacks else "none"
        mal_pct = d.get("mal_ratio", 0) * 100

        desc = (
            f"IoT device at IP {d['ip']} from {d.get('dataset', 'unknown')} dataset. "
            f"Role: {d.get('role', 'unknown')}. "
            f"Network activity: {d.get('degree', 0)} total connections, "
            f"communicates with {d.get('peers', 0)} peers, "
            f"uses {d.get('ports', 0)} distinct services. "
            f"Threat profile: {mal_pct:.1f}% malicious traffic ratio. "
            f"Attack types observed: {attack_str}. "
            f"Total flows: {d.get('flow_count', 0)}."
        )
        descriptions.append({"ip": d["ip"], "description": desc})

    return descriptions


def embed_device_nodes():
    """Generate and store text embeddings for all Device nodes."""
    logger.info("Generating text embeddings for Device nodes...")

    descriptions = generate_device_descriptions()
    if not descriptions:
        logger.warning("No device descriptions generated")
        return

    batch_size = 500
    total_embedded = 0
    for i in range(0, len(descriptions), batch_size):
        batch_descs = descriptions[i:i + batch_size]
        texts = [d["description"] for d in batch_descs]
        embeddings = get_gemini_embeddings(texts)
        
        batch_data = [
            {"ip": desc["ip"], "embedding": emb, "text_description": desc["description"]}
            for desc, emb in zip(batch_descs, embeddings)
        ]

        query = """
        UNWIND $batch AS row
        MATCH (d:Device {ip: row.ip})
        SET d.embedding = row.embedding,
            d.text_description = row.text_description
        """
        run_batch_query(query, batch_data)
        total_embedded += len(batch_data)
        if total_embedded % 50000 == 0:
            logger.info(f"  ...stored {total_embedded} device embeddings...")

    logger.info(f"Stored text embeddings for {total_embedded} Device nodes")


def embed_attack_type_nodes():
    """Generate and store text embeddings for AttackType nodes."""
    logger.info("Generating text embeddings for AttackType nodes...")

    query = """
    MATCH (a:AttackType)
    OPTIONAL MATCH (a)-[:BELONGS_TO]->(c:AttackCategory)
    OPTIONAL MATCH (a)-[:MAPS_TO]->(m:MITRETechnique)
    RETURN a.name as name,
           coalesce(a.description, a.name) as description,
           coalesce(c.name, 'Unknown') as category,
           coalesce(c.severity, 'unknown') as severity,
           m.technique_id as mitre_id,
           m.name as mitre_name,
           m.description as mitre_desc
    """
    attacks = run_query(query)

    descriptions = []
    for a in attacks:
        desc = (
            f"Attack type: {a['name']}. Category: {a['category']}. "
            f"Severity: {a['severity']}. "
        )
        if a.get('mitre_id'):
            desc += (
                f"MITRE ATT&CK: {a['mitre_id']} ({a.get('mitre_name', '')}). "
                f"{a.get('mitre_desc', '')}"
            )
        descriptions.append({"name": a["name"], "text": desc})

    if not descriptions:
        logger.warning("No attack descriptions generated")
        return

    texts = [d["text"] for d in descriptions]
    embeddings = get_gemini_embeddings(texts)

    batch_data = [
        {"name": desc["name"], "embedding": emb}
        for desc, emb in zip(descriptions, embeddings)
    ]

    query = """
    UNWIND $batch AS row
    MATCH (a:AttackType {name: row.name})
    SET a.embedding = row.embedding
    """
    run_batch_query(query, batch_data)
    logger.info(f"Stored text embeddings for {len(batch_data)} AttackType nodes")


def embed_mitre_nodes():
    """Generate and store text embeddings for MITRETechnique nodes."""
    logger.info("Generating text embeddings for MITRETechnique nodes...")

    query = """
    MATCH (m:MITRETechnique)
    RETURN m.technique_id as id,
           m.name as name,
           m.tactic as tactic,
           m.description as description
    """
    techniques = run_query(query)

    if not techniques:
        logger.warning("No MITRE techniques found")
        return

    texts = [
        f"MITRE ATT&CK Technique {t['id']}: {t['name']}. "
        f"Tactic: {t['tactic']}. {t['description']}"
        for t in techniques
    ]

    embeddings = get_gemini_embeddings(texts)

    batch_data = [
        {"id": t["id"], "embedding": emb}
        for t, emb in zip(techniques, embeddings)
    ]

    query = """
    UNWIND $batch AS row
    MATCH (m:MITRETechnique {technique_id: row.id})
    SET m.embedding = row.embedding
    """
    run_batch_query(query, batch_data)
    logger.info(f"Stored text embeddings for {len(batch_data)} MITRETechnique nodes")


# --------------------------------------------------------------------------
# Graph Structural Embeddings via Node2Vec
# --------------------------------------------------------------------------

def compute_node2vec_embeddings():
    """Compute node2vec structural embeddings and store in Neo4j."""
    from src.services.graph_embeddings.node2vec_embeddings import compute_node2vec

    edges_query = """
    MATCH (src:Device)-[r:COMMUNICATES_WITH]->(dst:Device)
    RETURN src.ip AS source, dst.ip AS target, r.flow_count AS weight
    """
    edges = run_query(edges_query)
    if not edges:
        logger.warning("No edges found for node2vec")
        return

    edge_list = [(e["source"], e["target"], e.get("weight", 1)) for e in edges]
    embeddings = compute_node2vec(edge_list)
    logger.info(f"Computed node2vec embeddings for {len(embeddings)} nodes")

    batch_data = [{"ip": ip, "structural_embedding": vec} for ip, vec in embeddings.items()]
    run_batch_query("""
        UNWIND $batch AS row
        MATCH (d:Device {ip: row.ip})
        SET d.structural_embedding = row.structural_embedding
    """, batch_data)
    logger.info(f"Stored structural embeddings for {len(batch_data)} Device nodes")


# --------------------------------------------------------------------------
# Combined Embedding Pipeline
# --------------------------------------------------------------------------

def generate_all_embeddings():
    """Run the complete embedding generation pipeline."""
    logger.info("=" * 60)
    logger.info("  Stage 4: Embedding Generation")
    logger.info("=" * 60)

    if not verify_connectivity():
        return False

    # Text embeddings (sentence-transformers)
    embed_device_nodes()
    embed_attack_type_nodes()
    embed_mitre_nodes()

    # Structural embeddings (Node2Vec / Spectral)
    compute_node2vec_embeddings()

    # Verify
    result = run_query("""
        MATCH (d:Device) WHERE d.embedding IS NOT NULL
        RETURN count(d) as text_embedded
    """)
    text_count = result[0]["text_embedded"] if result else 0

    result = run_query("""
        MATCH (d:Device) WHERE d.structural_embedding IS NOT NULL
        RETURN count(d) as struct_embedded
    """)
    struct_count = result[0]["struct_embedded"] if result else 0

    logger.info(f"\nEmbedding Summary:")
    logger.info(f"  Text embeddings (sentence-transformers): {text_count} devices")
    logger.info(f"  Structural embeddings (ASE):    {struct_count} devices")

    return True


if __name__ == "__main__":
    generate_all_embeddings()
