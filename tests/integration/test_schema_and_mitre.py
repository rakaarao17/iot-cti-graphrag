"""Integration tests for schema setup and MITRE enrichment (require live Neo4j)."""
import pytest
from src.services.knowledge_graph.neo4j_connection import run_query, verify_connectivity
from src.services.knowledge_graph.schema_setup import setup_full_schema
from src.services.knowledge_graph.enrich_mitre import enrich_with_mitre


@pytest.fixture(scope="module")
def neo4j_available():
    if not verify_connectivity():
        pytest.skip("Neo4j not available")


def test_schema_setup_creates_constraints(neo4j_available):
    result = setup_full_schema()
    assert result is True

    constraints = run_query("SHOW CONSTRAINTS")
    constraint_names = [c.get("name", "") for c in constraints]
    assert any("attack_name" in n for n in constraint_names)
    assert any("protocol_name" in n for n in constraint_names)


def test_schema_setup_creates_vector_indexes(neo4j_available):
    indexes = run_query("SHOW INDEXES")
    vector_indexes = [i for i in indexes if i.get("type") == "VECTOR"]
    assert len(vector_indexes) >= 2, f"Expected >=2 vector indexes, got: {vector_indexes}"


def test_mitre_enrichment_loads_techniques(neo4j_available):
    enrich_with_mitre()
    result = run_query("MATCH (m:MITRETechnique) RETURN count(m) AS cnt")
    count = result[0]["cnt"]
    assert count >= 10, f"Expected >=10 MITRE techniques, got {count}"


def test_mitre_techniques_have_required_fields(neo4j_available):
    result = run_query("""
        MATCH (m:MITRETechnique)
        WHERE m.technique_id IS NULL OR m.name IS NULL OR m.tactic IS NULL
        RETURN count(m) AS incomplete
    """)
    assert result[0]["incomplete"] == 0, "Some MITRETechnique nodes are missing required fields"
