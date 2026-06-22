"""
Stage 3: MITRE ATT&CK Enrichment.

Maps attack types in the Knowledge Graph to MITRE ATT&CK techniques,
creating MITRETechnique nodes and MAPS_TO relationships.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import logger
from config.schema import MITRE_ATTACK_MAP, ATTACK_CATEGORY_MAP
from src.services.knowledge_graph.neo4j_connection import (
    run_write_query, run_batch_query, run_query, verify_connectivity
)


def create_mitre_technique_nodes():
    """Create MITRETechnique nodes from the MITRE ATT&CK mapping."""
    techniques = []
    for category, info in MITRE_ATTACK_MAP.items():
        techniques.append({
            "technique_id": info["technique_id"],
            "name": info["name"],
            "tactic": info["tactic"],
            "description": info["description"],
            "url": info["url"],
            "category": category,
        })

    query = """
    UNWIND $batch AS row
    MERGE (m:MITRETechnique {technique_id: row.technique_id})
    SET m.name = row.name,
        m.tactic = row.tactic,
        m.description = row.description,
        m.url = row.url
    """
    run_batch_query(query, techniques)
    logger.info(f"Created {len(techniques)} MITRETechnique nodes")


def link_attacks_to_mitre():
    """
    Create MAPS_TO relationships between AttackType and MITRETechnique nodes.

    Uses the ATTACK_CATEGORY_MAP to find the category for each attack type,
    then links to the corresponding MITRE technique.
    """
    # Build a mapping: attack_type_name â†’ MITRE technique_id
    attack_to_mitre = []
    for attack_label, category in ATTACK_CATEGORY_MAP.items():
        if category in MITRE_ATTACK_MAP:
            attack_to_mitre.append({
                "attack_name": attack_label,
                "technique_id": MITRE_ATTACK_MAP[category]["technique_id"],
            })

    query = """
    UNWIND $batch AS row
    MATCH (a:AttackType {name: row.attack_name})
    MATCH (m:MITRETechnique {technique_id: row.technique_id})
    MERGE (a)-[:MAPS_TO]->(m)
    """

    if attack_to_mitre:
        run_batch_query(query, attack_to_mitre)
        logger.info(f"Linked {len(attack_to_mitre)} AttackType â†’ MITRETechnique mappings")
    else:
        logger.warning("No attack types found to link to MITRE techniques")


def add_mitre_context_descriptions():
    """
    Enrich AttackType nodes with MITRE-informed descriptions
    for better GraphRAG retrieval.
    """
    query = """
    MATCH (a:AttackType)-[:MAPS_TO]->(m:MITRETechnique)
    MATCH (a)-[:BELONGS_TO]->(c:AttackCategory)
    SET a.description = a.name + ' is a type of ' + c.name + ' attack. ' +
        'It maps to MITRE ATT&CK technique ' + m.technique_id + ' (' + m.name + ') ' +
        'in the ' + m.tactic + ' tactic phase. ' + m.description,
        a.severity = c.severity
    """
    run_write_query(query)
    logger.info("Enriched AttackType descriptions with MITRE context")


def get_mitre_summary():
    """Get a summary of MITRE ATT&CK coverage in the knowledge graph."""
    query = """
    MATCH (m:MITRETechnique)<-[:MAPS_TO]-(a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
    WITH m, a, count(f) as flow_count
    RETURN m.technique_id as technique_id,
           m.name as technique_name,
           m.tactic as tactic,
           collect(a.name) as attack_types,
           sum(flow_count) as total_flows
    ORDER BY total_flows DESC
    """
    results = run_query(query)

    if results:
        print("\n" + "=" * 80)
        print("  MITRE ATT&CK Coverage Summary")
        print("=" * 80)
        for r in results:
            print(f"\n  {r['technique_id']} â€” {r['technique_name']}")
            print(f"  Tactic: {r['tactic']}")
            print(f"  Flows:  {r['total_flows']:,}")
            print(f"  Attack Types: {', '.join(r['attack_types'][:5])}")
            if len(r['attack_types']) > 5:
                print(f"                + {len(r['attack_types']) - 5} more")
        print("=" * 80)
    else:
        print("No MITRE ATT&CK mappings found. Run enrichment first.")

    return results


def enrich_with_mitre():
    """Run the complete MITRE ATT&CK enrichment pipeline."""
    logger.info("=" * 60)
    logger.info("  MITRE ATT&CK Enrichment")
    logger.info("=" * 60)

    if not verify_connectivity():
        return False

    create_mitre_technique_nodes()
    link_attacks_to_mitre()
    add_mitre_context_descriptions()
    get_mitre_summary()

    return True


if __name__ == "__main__":
    enrich_with_mitre()
