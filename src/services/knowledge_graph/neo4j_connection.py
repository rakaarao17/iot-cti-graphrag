"""
Stage 3: Neo4j Connection Manager.

Thread-safe Neo4j driver wrapper with connection pooling,
auto-reconnect, health checks, and batch query execution.
"""

import sys
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE, NEO4J_MAX_RETRIES, logger

# Module-level driver singleton
_driver = None


def get_driver():
    """Get or create the Neo4j driver singleton."""
    global _driver
    if _driver is None:
        try:
            _driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=30,
            )
            logger.info(f"Neo4j driver created: {NEO4J_URI}")
        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {e}")
            raise
    return _driver


def close_driver():
    """Close the Neo4j driver."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


def verify_connectivity() -> bool:
    """Test the Neo4j connection."""
    try:
        driver = get_driver()
        driver.verify_connectivity()
        logger.info("[OK] Neo4j connection verified successfully")
        return True
    except AuthError as e:
        logger.error(f"[FAIL] Neo4j authentication failed: {e}")
        return False
    except ServiceUnavailable as e:
        logger.error(f"[FAIL] Neo4j service unavailable: {e}")
        logger.info("  Ensure Neo4j is running: neo4j console")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Neo4j connection failed: {e}")
        return False


@contextmanager
def get_session(database: str = NEO4J_DATABASE):
    """Get a Neo4j session with automatic cleanup."""
    driver = get_driver()
    session = driver.session(database=database)
    try:
        yield session
    finally:
        session.close()


def run_query(
    query: str,
    parameters: Dict[str, Any] = None,
    database: str = NEO4J_DATABASE,
) -> List[Dict]:
    """
    Execute a single Cypher query and return results as list of dicts.

    Args:
        query: Cypher query string
        parameters: Query parameters
        database: Neo4j database name

    Returns:
        List of result records as dictionaries
    """
    with get_session(database) as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


def run_query_single(
    query: str,
    parameters: Dict[str, Any] = None,
    database: str = NEO4J_DATABASE,
) -> Optional[Dict]:
    """Execute a query and return the first result."""
    results = run_query(query, parameters, database)
    return results[0] if results else None


def run_write_query(
    query: str,
    parameters: Dict[str, Any] = None,
    database: str = NEO4J_DATABASE,
    retries: int = None,
) -> Dict:
    """
    Execute a write query with retry logic.

    Returns:
        Summary counters dict
    """
    retries = retries or NEO4J_MAX_RETRIES

    for attempt in range(retries):
        try:
            with get_session(database) as session:
                result = session.run(query, parameters or {})
                summary = result.consume()
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_created": summary.counters.relationships_created,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set,
                }
        except ServiceUnavailable as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Neo4j unavailable, retrying in {wait}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            logger.error(f"Write query failed: {e}")
            raise


def run_batch_query(
    query: str,
    batch_data: List[Dict],
    batch_param_name: str = "batch",
    database: str = NEO4J_DATABASE,
) -> Dict:
    """
    Execute a query with UNWIND over batch data for efficient bulk operations.

    Args:
        query: Cypher query using UNWIND $batch AS row
        batch_data: List of dicts to pass as the batch parameter
        batch_param_name: Parameter name for the batch (default: "batch")
        database: Neo4j database name

    Returns:
        Aggregated summary counters
    """
    return run_write_query(query, {batch_param_name: batch_data}, database)


def get_node_count(label: str = None) -> int:
    """Get the count of nodes, optionally filtered by label."""
    if label:
        result = run_query_single(f"MATCH (n:{label}) RETURN count(n) as count")
    else:
        result = run_query_single("MATCH (n) RETURN count(n) as count")
    return result["count"] if result else 0


def get_relationship_count(rel_type: str = None) -> int:
    """Get the count of relationships, optionally filtered by type."""
    if rel_type:
        result = run_query_single(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
    else:
        result = run_query_single("MATCH ()-[r]->() RETURN count(r) as count")
    return result["count"] if result else 0


def get_database_stats() -> Dict:
    """Get comprehensive database statistics."""
    stats = {}

    # Node counts by label
    labels_result = run_query("CALL db.labels() YIELD label RETURN label")
    stats["nodes"] = {}
    for record in labels_result:
        label = record["label"]
        count = get_node_count(label)
        stats["nodes"][label] = count

    # Relationship counts by type
    rels_result = run_query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
    stats["relationships"] = {}
    for record in rels_result:
        rel_type = record["relationshipType"]
        count = get_relationship_count(rel_type)
        stats["relationships"][rel_type] = count

    stats["total_nodes"] = sum(stats["nodes"].values())
    stats["total_relationships"] = sum(stats["relationships"].values())

    return stats


def clear_database(confirm: bool = False):
    """Delete all nodes and relationships. Requires explicit confirmation."""
    if not confirm:
        logger.warning("clear_database() requires confirm=True. This is destructive!")
        return

    logger.warning("Clearing entire Neo4j database...")
    run_write_query("MATCH (n) DETACH DELETE n")
    logger.info("Database cleared")


def print_database_stats():
    """Print formatted database statistics."""
    stats = get_database_stats()
    print("\n" + "=" * 50)
    print("  Neo4j Database Statistics")
    print("=" * 50)
    print(f"\n  Nodes ({stats['total_nodes']:,} total):")
    for label, count in sorted(stats["nodes"].items()):
        print(f"    {label:25s} {count:8,d}")
    print(f"\n  Relationships ({stats['total_relationships']:,} total):")
    for rel, count in sorted(stats["relationships"].items()):
        print(f"    {rel:25s} {count:8,d}")
    print("=" * 50)


if __name__ == "__main__":
    if verify_connectivity():
        print_database_stats()
    close_driver()
