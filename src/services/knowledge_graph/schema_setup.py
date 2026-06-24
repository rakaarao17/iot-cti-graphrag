"""
Stage 3: Neo4j Schema Setup.

Creates constraints, indexes, and vector indexes in Neo4j
for the IoT CTI Knowledge Graph.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import EMBEDDING_DIMENSION, logger
from src.services.knowledge_graph.neo4j_connection import run_write_query, run_query, verify_connectivity


def create_constraints():
    """Create uniqueness constraints for key node properties."""
    constraints = [
        ("device_ip",         "CREATE CONSTRAINT device_ip IF NOT EXISTS FOR (d:Device) REQUIRE d.ip IS UNIQUE"),
        ("attack_name",       "CREATE CONSTRAINT attack_name IF NOT EXISTS FOR (a:AttackType) REQUIRE a.name IS UNIQUE"),
        ("category_name",     "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:AttackCategory) REQUIRE c.name IS UNIQUE"),
        ("protocol_name",     "CREATE CONSTRAINT protocol_name IF NOT EXISTS FOR (p:Protocol) REQUIRE p.name IS UNIQUE"),
        ("port_number",       "CREATE CONSTRAINT port_number IF NOT EXISTS FOR (p:Port) REQUIRE p.number IS UNIQUE"),
        ("mitre_id",          "CREATE CONSTRAINT mitre_id IF NOT EXISTS FOR (m:MITRETechnique) REQUIRE m.technique_id IS UNIQUE"),
        ("dataset_name",      "CREATE CONSTRAINT dataset_name IF NOT EXISTS FOR (d:Dataset) REQUIRE d.name IS UNIQUE"),
    ]

    logger.info("Creating uniqueness constraints...")
    for name, query in constraints:
        try:
            run_write_query(query)
            logger.info(f"  âœ“ Constraint: {name}")
        except Exception as e:
            if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                logger.info(f"  â—‹ Constraint already exists: {name}")
            else:
                logger.warning(f"  âœ— Constraint failed: {name} â€” {e}")


def create_indexes():
    """Create performance indexes for common query patterns."""
    indexes = [
        # Flow queries
        ("flow_uid",        "CREATE INDEX flow_uid IF NOT EXISTS FOR (f:Flow) ON (f.uid)"),
        ("flow_timestamp",  "CREATE INDEX flow_timestamp IF NOT EXISTS FOR (f:Flow) ON (f.timestamp)"),
        ("flow_label",      "CREATE INDEX flow_label IF NOT EXISTS FOR (f:Flow) ON (f.label)"),
        ("flow_dataset",    "CREATE INDEX flow_dataset IF NOT EXISTS FOR (f:Flow) ON (f.dataset)"),
        # Device queries
        ("device_dataset",  "CREATE INDEX device_dataset IF NOT EXISTS FOR (d:Device) ON (d.dataset)"),
        ("device_role",     "CREATE INDEX device_role IF NOT EXISTS FOR (d:Device) ON (d.role)"),
        # Composite indexes
        ("flow_src_dst",    "CREATE INDEX flow_src_dst IF NOT EXISTS FOR (f:Flow) ON (f.src_ip, f.dst_ip)"),
    ]

    logger.info("Creating performance indexes...")
    for name, query in indexes:
        try:
            run_write_query(query)
            logger.info(f"  âœ“ Index: {name}")
        except Exception as e:
            if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                logger.info(f"  â—‹ Index already exists: {name}")
            else:
                logger.warning(f"  âœ— Index failed: {name} â€” {e}")


def create_vector_indexes():
    """Create vector indexes for embedding-based retrieval (GraphRAG)."""
    vector_indexes = [
        (
            "device_embedding",
            f"""CREATE VECTOR INDEX device_embedding IF NOT EXISTS
            FOR (d:Device) ON (d.embedding)
            OPTIONS {{indexConfig: {{
                `vector.dimensions`: {EMBEDDING_DIMENSION},
                `vector.similarity_function`: 'cosine'
            }}}}"""
        ),
        (
            "attack_embedding",
            f"""CREATE VECTOR INDEX attack_embedding IF NOT EXISTS
            FOR (a:AttackType) ON (a.embedding)
            OPTIONS {{indexConfig: {{
                `vector.dimensions`: {EMBEDDING_DIMENSION},
                `vector.similarity_function`: 'cosine'
            }}}}"""
        ),
        (
            "mitre_embedding",
            f"""CREATE VECTOR INDEX mitre_embedding IF NOT EXISTS
            FOR (m:MITRETechnique) ON (m.embedding)
            OPTIONS {{indexConfig: {{
                `vector.dimensions`: {EMBEDDING_DIMENSION},
                `vector.similarity_function`: 'cosine'
            }}}}"""
        ),
        (
            "flow_embedding",
            f"""CREATE VECTOR INDEX flow_embedding IF NOT EXISTS
            FOR (f:Flow) ON (f.embedding)
            OPTIONS {{indexConfig: {{
                `vector.dimensions`: {EMBEDDING_DIMENSION},
                `vector.similarity_function`: 'cosine'
            }}}}"""
        ),
    ]

    logger.info("Creating vector indexes for GraphRAG...")
    for name, query in vector_indexes:
        try:
            run_write_query(query)
            logger.info(f"  âœ“ Vector Index: {name}")
        except Exception as e:
            if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                logger.info(f"  â—‹ Vector index already exists: {name}")
            else:
                logger.warning(f"  âœ— Vector index failed: {name} â€” {e}")
                logger.info("    (Vector indexes require Neo4j 5.11+ Enterprise or Aura)")


def setup_full_schema():
    """Run the complete schema setup."""
    logger.info("=" * 60)
    logger.info("  Neo4j Schema Setup")
    logger.info("=" * 60)

    if not verify_connectivity():
        logger.error("Cannot setup schema â€” Neo4j not available")
        return False

    create_constraints()
    create_indexes()
    create_vector_indexes()

    # Verify
    constraints_result = run_query("SHOW CONSTRAINTS")
    indexes_result = run_query("SHOW INDEXES")

    logger.info(f"\nSchema Setup Complete:")
    logger.info(f"  Constraints: {len(constraints_result)}")
    logger.info(f"  Indexes:     {len(indexes_result)}")

    return True


if __name__ == "__main__":
    setup_full_schema()
