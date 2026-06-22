"""
Stage 4: Pre-built Analytical Cypher Queries.

A library of Cypher queries for analyzing the IoT CTI Knowledge Graph,
covering attack patterns, device behavior, and temporal analysis.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import logger
from src.services.knowledge_graph.neo4j_connection import run_query


# â”€â”€ Attack Analysis Queries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_top_attackers(limit: int = 20) -> List[Dict]:
    """Get devices with the highest count of malicious flows."""
    query = """
    MATCH (d:Device)-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
    WHERE a.name <> 'Benign'
    WITH d, count(f) as malicious_flows,
         collect(DISTINCT a.name) as attack_types,
         sum(f.orig_bytes + f.resp_bytes) as total_bytes
    RETURN d.ip as ip,
           malicious_flows,
           attack_types,
           total_bytes,
           size(attack_types) as attack_diversity
    ORDER BY malicious_flows DESC
    LIMIT $limit
    """
    return run_query(query, {"limit": limit})


def get_most_targeted_devices(limit: int = 20) -> List[Dict]:
    """Get devices most frequently targeted by attacks."""
    query = """
    MATCH (f:Flow)-[:TARGETS]->(d:Device)
    MATCH (f)-[:CLASSIFIED_AS]->(a:AttackType)
    WHERE a.name <> 'Benign'
    WITH d, count(f) as incoming_attacks,
         collect(DISTINCT a.name) as attack_types_received
    RETURN d.ip as ip,
           incoming_attacks,
           attack_types_received,
           size(attack_types_received) as attack_type_count
    ORDER BY incoming_attacks DESC
    LIMIT $limit
    """
    return run_query(query, {"limit": limit})


def get_attack_distribution() -> List[Dict]:
    """Get the distribution of attack types across all flows."""
    query = """
    MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
    MATCH (a)-[:BELONGS_TO]->(c:AttackCategory)
    WITH c.name as category, a.name as attack_type,
         count(f) as flow_count,
         c.severity as severity
    RETURN category, attack_type, flow_count, severity
    ORDER BY flow_count DESC
    """
    return run_query(query)


def get_attack_chains(device_ip: str) -> List[Dict]:
    """Get the sequence of attack types for a specific device."""
    query = """
    MATCH (d:Device {ip: $ip})-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
    WITH f, a
    ORDER BY f.timestamp
    RETURN f.timestamp as timestamp,
           a.name as attack_type,
           f.duration as duration,
           f.orig_bytes as bytes_sent,
           f.resp_bytes as bytes_received
    LIMIT 100
    """
    return run_query(query, {"ip": device_ip})


# â”€â”€ Network Topology Queries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_communication_clusters(min_flows: int = 5) -> List[Dict]:
    """Find devices that communicate frequently (potential botnets)."""
    query = """
    MATCH (src:Device)-[r:COMMUNICATES_WITH]->(dst:Device)
    WHERE r.flow_count >= $min_flows
    RETURN src.ip as source,
           dst.ip as target,
           r.flow_count as flow_count,
           r.total_bytes as total_bytes,
           r.attack_types as attack_types
    ORDER BY r.flow_count DESC
    LIMIT 50
    """
    return run_query(query, {"min_flows": min_flows})


def get_port_scan_suspects(min_unique_ports: int = 10) -> List[Dict]:
    """Find devices connecting to many distinct destination ports (port scanning)."""
    query = """
    MATCH (d:Device)-[:INITIATES]->(f:Flow)-[:TARGETS]->(t:Device)
    WITH d, t, collect(DISTINCT f.service) as services,
         count(DISTINCT f.uid) as flow_count
    WHERE flow_count >= $min_ports
    RETURN d.ip as scanner_ip,
           t.ip as target_ip,
           flow_count,
           services
    ORDER BY flow_count DESC
    LIMIT 20
    """
    return run_query(query, {"min_ports": min_unique_ports})


def get_device_profile(device_ip: str) -> Dict:
    """Get a comprehensive profile of a single device."""
    query = """
    MATCH (d:Device {ip: $ip})
    OPTIONAL MATCH (d)-[:INITIATES]->(f_out:Flow)
    WITH d, count(f_out) as outgoing_flows, sum(f_out.orig_bytes) as total_bytes_sent
    
    OPTIONAL MATCH (f_in:Flow)-[:TARGETS]->(d)
    WITH d, outgoing_flows, total_bytes_sent, count(f_in) as incoming_flows
    
    OPTIONAL MATCH (d)-[:INITIATES]->(f_mal:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
    WHERE a.name <> 'Benign'
    WITH d, outgoing_flows, total_bytes_sent, incoming_flows, 
         count(f_mal) as malicious_flows, collect(DISTINCT a.name) as attack_types
         
    OPTIONAL MATCH (d)-[:COMMUNICATES_WITH]->(peer:Device)
    WITH d, outgoing_flows, total_bytes_sent, incoming_flows, 
         malicious_flows, attack_types, collect(DISTINCT peer.ip) as peers
         
    RETURN d.ip as ip,
           d.role as role,
           d.dataset as dataset,
           d.first_seen as first_seen,
           d.last_seen as last_seen,
           outgoing_flows,
           incoming_flows,
           malicious_flows,
           attack_types,
           size(peers) as peer_count,
           peers[..10] as top_peers,
           total_bytes_sent
    """
    results = run_query(query, {"ip": device_ip})
    return results[0] if results else {}


# â”€â”€ MITRE ATT&CK Queries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_mitre_coverage() -> List[Dict]:
    """Get MITRE ATT&CK technique coverage across the dataset."""
    query = """
    MATCH (m:MITRETechnique)<-[:MAPS_TO]-(a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
    WITH m, count(DISTINCT a) as attack_types, count(f) as total_flows
    RETURN m.technique_id as technique_id,
           m.name as technique_name,
           m.tactic as tactic,
           attack_types,
           total_flows
    ORDER BY total_flows DESC
    """
    return run_query(query)


def get_attack_to_mitre_path(attack_name: str) -> List[Dict]:
    """Get the full path from an attack type to its MITRE technique."""
    query = """
    MATCH (a:AttackType {name: $name})-[:BELONGS_TO]->(c:AttackCategory)
    OPTIONAL MATCH (a)-[:MAPS_TO]->(m:MITRETechnique)
    RETURN a.name as attack_type,
           a.description as description,
           c.name as category,
           c.severity as severity,
           m.technique_id as mitre_id,
           m.name as mitre_name,
           m.tactic as mitre_tactic,
           m.url as mitre_url
    """
    results = run_query(query, {"name": attack_name})
    return results[0] if results else {}


# â”€â”€ Dataset Comparison Queries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def compare_datasets() -> List[Dict]:
    """Compare attack distributions between IoT-23 and CICIoT2023."""
    query = """
    MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)-[:BELONGS_TO]->(c:AttackCategory)
    WITH f.dataset as dataset, c.name as category, count(f) as count
    RETURN dataset, category, count
    ORDER BY dataset, count DESC
    """
    return run_query(query)


# â”€â”€ Graph Statistics Queries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_graph_summary() -> Dict:
    """Get a high-level summary of the knowledge graph."""
    queries = {
        "total_devices": "MATCH (d:Device) RETURN count(d) as count",
        "total_flows": "MATCH (f:Flow) RETURN count(f) as count",
        "total_attack_types": "MATCH (a:AttackType) RETURN count(a) as count",
        "total_mitre_techniques": "MATCH (m:MITRETechnique) RETURN count(m) as count",
        "malicious_flows": "MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType) WHERE a.name <> 'Benign' RETURN count(f) as count",
        "benign_flows": "MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType {name: 'Benign'}) RETURN count(f) as count",
    }

    summary = {}
    for key, query in queries.items():
        result = run_query(query)
        summary[key] = result[0]["count"] if result else 0

    return summary


def print_full_analysis():
    """Print a comprehensive analysis of the knowledge graph."""
    print("\n" + "=" * 70)
    print("  IoT CTI Knowledge Graph â€” Full Analysis")
    print("=" * 70)

    # Summary
    summary = get_graph_summary()
    print(f"\n  ðŸ“Š Graph Summary")
    print(f"  {'â”€' * 50}")
    for key, value in summary.items():
        print(f"    {key.replace('_', ' ').title():30s} {value:,}")

    # Top attackers
    print(f"\n  ðŸ”´ Top 10 Attackers")
    print(f"  {'â”€' * 50}")
    for r in get_top_attackers(10):
        print(f"    {r['ip']:20s} {r['malicious_flows']:6,} flows  "
              f"({r['attack_diversity']} attack types)")

    # Attack distribution
    print(f"\n  âš ï¸  Attack Distribution")
    print(f"  {'â”€' * 50}")
    for r in get_attack_distribution()[:15]:
        print(f"    [{r['severity']:8s}] {r['attack_type']:35s} {r['flow_count']:8,}")

    print("=" * 70)


if __name__ == "__main__":
    print_full_analysis()
