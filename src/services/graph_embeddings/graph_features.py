"""
Stage 4: Graph-Structural Feature Extraction.

Extracts structural features from the Knowledge Graph for each device:
degree centrality, PageRank approximation, malicious flow ratios, etc.
These features are stored as node properties for later use in embeddings.
"""

import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import logger
from src.services.knowledge_graph.neo4j_connection import (
    run_query, run_write_query, verify_connectivity
)


def compute_device_degree():
    """
    Compute in-degree, out-degree, and total degree for each Device.
    Stored as properties on Device nodes.
    """
    query = """
    MATCH (d:Device)
    OPTIONAL MATCH (d)-[:INITIATES]->(f_out:Flow)
    WITH d, count(DISTINCT f_out) as out_degree
    OPTIONAL MATCH (f_in:Flow)-[:TARGETS]->(d)
    WITH d, out_degree, count(DISTINCT f_in) as in_degree
    SET d.out_degree = out_degree,
        d.in_degree = in_degree,
        d.total_degree = out_degree + in_degree
    """
    run_write_query(query)
    logger.info("âœ“ Computed device degree centrality")


def compute_malicious_ratios():
    """
    Compute the ratio of malicious vs benign flows for each device.
    """
    query = """
    MATCH (d:Device)-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
    WITH d,
         count(f) as total_flows,
         sum(CASE WHEN a.name <> 'Benign' THEN 1 ELSE 0 END) as malicious_count,
         collect(DISTINCT a.name) as attack_types
    SET d.total_flows = total_flows,
        d.malicious_count = malicious_count,
        d.malicious_ratio = CASE WHEN total_flows > 0
                                 THEN toFloat(malicious_count) / total_flows
                                 ELSE 0.0 END,
        d.attack_types = attack_types,
        d.attack_diversity = size(attack_types)
    """
    run_write_query(query)
    logger.info("âœ“ Computed malicious flow ratios")


def compute_port_diversity():
    """
    Compute the number of unique destination ports each device connects to.
    High port diversity may indicate scanning behavior.
    """
    query = """
    MATCH (d:Device)-[:INITIATES]->(f:Flow)
    WITH d, collect(DISTINCT f.service) as services
    SET d.port_diversity = size(services),
        d.services = services[..20]
    """
    run_write_query(query)
    logger.info("âœ“ Computed port diversity")


def compute_peer_count():
    """
    Compute the number of unique peer devices each device communicates with.
    """
    query = """
    MATCH (d:Device)-[:COMMUNICATES_WITH]->(peer:Device)
    WITH d, count(DISTINCT peer) as peer_count
    SET d.peer_count = peer_count
    """
    run_write_query(query)
    logger.info("âœ“ Computed peer counts")


def compute_traffic_features():
    """
    Compute aggregate traffic features: total bytes, avg duration, etc.
    """
    query = """
    MATCH (d:Device)-[:INITIATES]->(f:Flow)
    WITH d,
         sum(f.orig_bytes) as total_bytes_sent,
         sum(f.resp_bytes) as total_bytes_received,
         avg(f.duration) as avg_duration,
         max(f.duration) as max_duration,
         avg(f.orig_bytes) as avg_bytes_per_flow
    SET d.total_bytes_sent = toInteger(total_bytes_sent),
        d.total_bytes_received = toInteger(total_bytes_received),
        d.avg_duration = toFloat(avg_duration),
        d.max_duration = toFloat(max_duration),
        d.avg_bytes_per_flow = toFloat(avg_bytes_per_flow)
    """
    run_write_query(query)
    logger.info("âœ“ Computed aggregate traffic features")


def compute_temporal_features():
    """
    Compute temporal features: active time window, flow rate.
    """
    query = """
    MATCH (d:Device)-[:INITIATES]->(f:Flow)
    WITH d,
         min(f.timestamp) as first_ts,
         max(f.timestamp) as last_ts,
         count(f) as flow_count
    WITH d, first_ts, last_ts, flow_count,
         CASE WHEN last_ts > first_ts
              THEN toFloat(flow_count) / (last_ts - first_ts)
              ELSE toFloat(flow_count) END as flow_rate
    SET d.first_seen = first_ts,
        d.last_seen = last_ts,
        d.active_duration = last_ts - first_ts,
        d.flow_rate = flow_rate
    """
    run_write_query(query)
    logger.info("âœ“ Computed temporal features")


def compute_all_graph_features():
    """Run all graph feature computations."""
    logger.info("=" * 60)
    logger.info("  Stage 4: Graph-Structural Feature Extraction")
    logger.info("=" * 60)

    if not verify_connectivity():
        return False

    compute_device_degree()
    compute_malicious_ratios()
    compute_port_diversity()
    compute_peer_count()
    compute_traffic_features()
    compute_temporal_features()

    # Verify features were set
    result = run_query("""
        MATCH (d:Device)
        WHERE d.total_degree IS NOT NULL
        RETURN count(d) as enriched_devices,
               avg(d.total_degree) as avg_degree,
               avg(d.malicious_ratio) as avg_mal_ratio,
               max(d.attack_diversity) as max_attack_diversity
    """)

    if result:
        r = result[0]
        logger.info(f"\n  Feature Extraction Summary:")
        logger.info(f"    Enriched devices:     {r['enriched_devices']:,}")
        logger.info(f"    Avg degree:           {r['avg_degree']:.1f}")
        logger.info(f"    Avg malicious ratio:  {r['avg_mal_ratio']:.3f}")
        logger.info(f"    Max attack diversity: {r['max_attack_diversity']}")

    return True


def get_device_feature_vectors() -> List[Dict]:
    """
    Export device feature vectors for use in graph embeddings.

    Returns a list of dicts with device IP and numeric features.
    """
    query = """
    MATCH (d:Device)
    WHERE d.total_degree IS NOT NULL
    RETURN d.ip as ip,
           coalesce(d.out_degree, 0) as out_degree,
           coalesce(d.in_degree, 0) as in_degree,
           coalesce(d.total_degree, 0) as total_degree,
           coalesce(d.malicious_ratio, 0.0) as malicious_ratio,
           coalesce(d.attack_diversity, 0) as attack_diversity,
           coalesce(d.port_diversity, 0) as port_diversity,
           coalesce(d.peer_count, 0) as peer_count,
           coalesce(d.total_bytes_sent, 0) as total_bytes_sent,
           coalesce(d.avg_duration, 0.0) as avg_duration,
           coalesce(d.flow_rate, 0.0) as flow_rate,
           coalesce(d.active_duration, 0.0) as active_duration
    ORDER BY d.malicious_ratio DESC
    """
    return run_query(query)


if __name__ == "__main__":
    compute_all_graph_features()

    # Print top suspicious devices
    devices = get_device_feature_vectors()
    print(f"\nTop 10 suspicious devices (by malicious ratio):")
    print(f"{'IP':20s} {'Degree':>8s} {'Mal.Ratio':>10s} {'Diversity':>10s} {'Peers':>8s}")
    print("-" * 60)
    for d in devices[:10]:
        print(f"{d['ip']:20s} {d['total_degree']:8d} {d['malicious_ratio']:10.3f} "
              f"{d['attack_diversity']:10d} {d['peer_count']:8d}")
