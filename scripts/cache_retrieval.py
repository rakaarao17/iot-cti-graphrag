"""
Build retrieval cache for LLM comparison benchmark.

Queries the live Neo4j graph (Cypher-based) for each benchmark query
and saves the retrieved context to data/eval/retrieval_cache.json.

Usage:
    python scripts/cache_retrieval.py --benchmark data/eval/comparison_benchmark.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_DATABASE = "iot"


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_attack_context(session) -> str:
    """Get top attack types with MITRE mappings and flow counts."""
    rows = session.run("""
        MATCH (a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
        WHERE a.name <> 'Benign'
        WITH a, count(f) AS flow_cnt
        OPTIONAL MATCH (a)-[:MAPS_TO]->(m:MITRETechnique)
        RETURN a.name AS attack,
               flow_cnt,
               collect(DISTINCT m.technique_id + ': ' + m.name)[0] AS mitre
        ORDER BY flow_cnt DESC
        LIMIT 10
    """).data()

    lines = ["=== Attack Type Summary ==="]
    for r in rows:
        mitre_str = f" [{r['mitre']}]" if r['mitre'] else ""
        lines.append(f"  {r['attack']}: {r['flow_cnt']:,} flows{mitre_str}")
    return "\n".join(lines)


def get_device_context(session, top_n: int = 8) -> str:
    """Get most active attacking devices."""
    rows = session.run("""
        MATCH (d:Device)-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
        WHERE a.name <> 'Benign' AND d.ip <> '0.0.0.0'
        WITH d.ip AS device_ip, collect(DISTINCT a.name) AS attack_types, count(f) AS cnt
        RETURN device_ip, attack_types[0..3] AS attacks, cnt
        ORDER BY cnt DESC
        LIMIT $top_n
    """, top_n=top_n).data()

    if not rows:
        return "=== Active Devices ===\n  No device data with IPs available."

    lines = ["=== Active Attacking Devices ==="]
    for r in rows:
        lines.append(f"  {r['device_ip']}: {r['cnt']:,} malicious flows | attacks: {', '.join(r['attacks'])}")
    return "\n".join(lines)


def get_mitre_context(session) -> str:
    """Get MITRE technique to attack mapping."""
    rows = session.run("""
        MATCH (a:AttackType)-[:MAPS_TO]->(m:MITRETechnique)
        RETURN m.technique_id AS tid, m.name AS tname,
               collect(DISTINCT a.name)[0..4] AS attacks
        ORDER BY tid
    """).data()

    lines = ["=== MITRE ATT&CK Mappings ==="]
    for r in rows:
        lines.append(f"  {r['tid']} ({r['tname']}): {', '.join(r['attacks'])}")
    return "\n".join(lines)


def get_ddos_context(session) -> str:
    """Context focused on DDoS attack patterns."""
    rows = session.run("""
        MATCH (a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
        WHERE a.name STARTS WITH 'DDoS' OR a.name STARTS WITH 'DoS'
        WITH a.name AS attack, count(f) AS cnt
        OPTIONAL MATCH (at:AttackType {name: attack})-[:MAPS_TO]->(m:MITRETechnique)
        RETURN attack, cnt, m.technique_id AS tid, m.name AS tname
        ORDER BY cnt DESC LIMIT 12
    """).data()

    lines = ["=== DDoS/DoS Attack Patterns ==="]
    for r in rows:
        mitre = f" | MITRE {r['tid']}: {r['tname']}" if r['tid'] else ""
        lines.append(f"  {r['attack']}: {r['cnt']:,} flows{mitre}")
    return "\n".join(lines)


def get_scan_context(session) -> str:
    """Context focused on scanning and reconnaissance."""
    rows = session.run("""
        MATCH (a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
        WHERE a.name CONTAINS 'Scan' OR a.name CONTAINS 'Recon'
              OR a.name CONTAINS 'Brute' OR a.name CONTAINS 'Mirai'
        WITH a.name AS attack, count(f) AS cnt
        OPTIONAL MATCH (at:AttackType {name: attack})-[:MAPS_TO]->(m:MITRETechnique)
        RETURN attack, cnt, m.technique_id AS tid, m.name AS tname
        ORDER BY cnt DESC
    """).data()

    lines = ["=== Scanning & Reconnaissance Patterns ==="]
    for r in rows:
        mitre = f" | MITRE {r['tid']}: {r['tname']}" if r['tid'] else ""
        lines.append(f"  {r['attack']}: {r['cnt']:,} flows{mitre}")
    return "\n".join(lines)


def get_malware_context(session) -> str:
    """Context for malware and C&C patterns."""
    rows = session.run("""
        MATCH (a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
        WHERE a.name CONTAINS 'Malware' OR a.name CONTAINS 'Backdoor'
              OR a.name CONTAINS 'C&C' OR a.name CONTAINS 'HeartBeat'
              OR a.name CONTAINS 'Injection' OR a.name CONTAINS 'Hijack'
        WITH a.name AS attack, count(f) AS cnt
        OPTIONAL MATCH (at:AttackType {name: attack})-[:MAPS_TO]->(m:MITRETechnique)
        RETURN attack, cnt, m.technique_id AS tid, m.name AS tname
        ORDER BY cnt DESC
    """).data()

    lines = ["=== Malware & C2 Communication Patterns ==="]
    for r in rows:
        mitre = f" | MITRE {r['tid']}: {r['tname']}" if r['tid'] else ""
        lines.append(f"  {r['attack']}: {r['cnt']:,} flows{mitre}")
    return "\n".join(lines)


def get_dataset_stats(session) -> str:
    """Dataset-level stats."""
    rows = session.run("""
        MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
        WITH a.name AS label, f.dataset AS dataset, count(*) AS cnt
        RETURN label, dataset, cnt
        ORDER BY cnt DESC LIMIT 15
    """).data()

    lines = ["=== Dataset Statistics ==="]
    for r in rows:
        lines.append(f"  [{r['dataset']}] {r['label']}: {r['cnt']:,} flows")
    return "\n".join(lines)


def get_protocol_context(session) -> str:
    """Protocol usage across attack types."""
    rows = session.run("""
        MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
        WHERE a.name <> 'Benign'
        WITH f.service AS svc, a.name AS attack, count(*) AS cnt
        WHERE svc IS NOT NULL
        RETURN svc, collect(DISTINCT attack)[0..3] AS attacks, sum(cnt) AS total
        ORDER BY total DESC LIMIT 8
    """).data()

    lines = ["=== Protocol / Service Patterns in Attacks ==="]
    if not rows:
        lines.append("  No service data available in flows.")
    for r in rows:
        lines.append(f"  {r['svc']}: {r['total']:,} flows | {', '.join(r['attacks'])}")
    return "\n".join(lines)


# Map from retrieval_type to context builder(s)
CONTEXT_BUILDERS = {
    "combined": ["attack", "mitre", "device", "dataset"],
    "cypher":   ["attack", "mitre", "device"],
    "vector":   ["attack", "mitre"],
}

CATEGORY_FOCUS = {
    "threat_explanation":    ["attack", "mitre", "device"],
    "incident_summary":      ["attack", "device", "dataset"],
    "attack_classification": ["attack", "mitre", "ddos", "scan"],
    "analyst_qa":            ["mitre", "attack", "malware", "scan"],
    "executive_summary":     ["attack", "dataset", "mitre"],
}


def build_context_for_query(session, query: dict) -> str:
    """Build rich retrieval context for a single benchmark query."""
    category = query.get("category", "threat_explanation")
    retrieval_type = query.get("retrieval_type", "combined")

    focus = CATEGORY_FOCUS.get(category, CATEGORY_FOCUS["threat_explanation"])

    parts = []
    parts.append(f"Query: {query['query']}\n")

    for key in focus:
        if key == "attack":
            parts.append(get_attack_context(session))
        elif key == "mitre":
            parts.append(get_mitre_context(session))
        elif key == "device":
            parts.append(get_device_context(session))
        elif key == "dataset":
            parts.append(get_dataset_stats(session))
        elif key == "ddos":
            parts.append(get_ddos_context(session))
        elif key == "scan":
            parts.append(get_scan_context(session))
        elif key == "malware":
            parts.append(get_malware_context(session))

    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Build GraphRAG retrieval cache from Neo4j")
    parser.add_argument("--benchmark", default="data/eval/comparison_benchmark.json")
    parser.add_argument("--output", default="data/eval/retrieval_cache.json")
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark)
    if not benchmark_path.exists():
        print(f"ERROR: Benchmark file not found: {benchmark_path}", file=sys.stderr)
        sys.exit(1)

    queries = json.loads(benchmark_path.read_text(encoding="utf-8"))
    print(f"Building retrieval cache for {len(queries)} queries...")

    driver = get_driver()
    cache = {}

    with driver.session(database=NEO4J_DATABASE) as session:
        for i, q in enumerate(queries, 1):
            qid = q.get("id", q.get("query_id", f"q{i}"))
            print(f"  [{i}/{len(queries)}] {qid}: {q['query'][:60]}...")
            context = build_context_for_query(session, q)
            cache[qid] = context

    driver.close()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    print(f"\nSaved retrieval cache: {output_path} ({len(cache)} entries)")


if __name__ == "__main__":
    main()
