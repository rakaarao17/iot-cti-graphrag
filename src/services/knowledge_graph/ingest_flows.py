"""
Stage 3: Ingest network flows into Neo4j Knowledge Graph.

Batch-imports flows from the unified CSV into Neo4j, creating:
- Device nodes (MERGE on IP)
- Flow nodes
- Protocol and Port nodes
- AttackType and AttackCategory nodes
- All relationships between them
- Aggregated COMMUNICATES_WITH edges
"""

import sys
import math
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    DATA_PROCESSED_DIR, DATA_SAMPLES_DIR, NEO4J_BATCH_SIZE, logger
)
from config.schema import ATTACK_CATEGORIES, WELL_KNOWN_PORTS
from src.services.knowledge_graph.neo4j_connection import (
    run_write_query, run_batch_query, run_query_single, verify_connectivity,
    print_database_stats
)


def create_dataset_nodes():
    """Create Dataset reference nodes."""
    datasets = [
        {
            "name": "IoT-23",
            "version": "v1",
            "source": "Stratosphere Lab, CTU Prague",
            "description": "23 scenarios of IoT malware and benign traffic with Zeek-labeled flows",
        },
        {
            "name": "CICIoT2023",
            "version": "2023",
            "source": "Canadian Institute for Cybersecurity, UNB",
            "description": "Network traffic from 105 real IoT devices with 33 attack types",
        },
    ]

    query = """
    UNWIND $batch AS row
    MERGE (d:Dataset {name: row.name})
    SET d.version = row.version,
        d.source = row.source,
        d.description = row.description
    """
    run_batch_query(query, datasets)
    logger.info(f"Created {len(datasets)} Dataset nodes")


def create_attack_category_nodes():
    """Create AttackCategory nodes from schema definitions."""
    categories = [
        {"name": name, "severity": info["severity"], "description": info["description"]}
        for name, info in ATTACK_CATEGORIES.items()
    ]

    query = """
    UNWIND $batch AS row
    MERGE (c:AttackCategory {name: row.name})
    SET c.severity = row.severity,
        c.description = row.description
    """
    run_batch_query(query, categories)
    logger.info(f"Created {len(categories)} AttackCategory nodes")


def create_protocol_nodes():
    """Create Protocol nodes."""
    protocols = [{"name": p} for p in ["TCP", "UDP", "ICMP", "OTHER"]]
    query = """
    UNWIND $batch AS row
    MERGE (p:Protocol {name: row.name})
    """
    run_batch_query(query, protocols)
    logger.info(f"Created {len(protocols)} Protocol nodes")


_FLOW_MERGE_QUERY = """
UNWIND $batch AS row
MERGE (src:Device {ip: row.src_ip})
  ON CREATE SET src.dataset = row.dataset, src.first_seen = row.uid
MERGE (dst:Device {ip: row.dst_ip})
  ON CREATE SET dst.dataset = row.dataset
MERGE (proto:Protocol {name: row.protocol})
MERGE (attack:AttackType {name: row.label})
CREATE (f:Flow {
    uid: row.uid,
    src_ip: row.src_ip,
    dst_ip: row.dst_ip,
    src_port: toInteger(row.src_port),
    dst_port: toInteger(row.dst_port),
    protocol: row.protocol,
    duration: toFloat(row.duration),
    fwd_pkts: toInteger(row.fwd_pkts),
    bwd_pkts: toInteger(row.bwd_pkts),
    fwd_bytes: toFloat(row.fwd_bytes),
    bwd_bytes: toFloat(row.bwd_bytes),
    label: row.label,
    dataset: row.dataset,
    timestamp: timestamp()
})
MERGE (f)-[:HAS_SOURCE]->(src)
MERGE (f)-[:HAS_DESTINATION]->(dst)
MERGE (f)-[:USES_PROTOCOL]->(proto)
MERGE (f)-[:CLASSIFIED_AS]->(attack)
MERGE (src)-[r:COMMUNICATES_WITH]->(dst)
  ON CREATE SET r.flow_count = 1
  ON MATCH SET r.flow_count = r.flow_count + 1
"""


def build_flow_batch(df: pd.DataFrame) -> list:
    """Convert DataFrame rows to list of dicts for Neo4j UNWIND."""
    return df.to_dict(orient="records")


def ingest_flows(df: pd.DataFrame, batch_size: int = 1000) -> int:
    """
    Ingest train flows into Neo4j.

    This function must ONLY be called with train data.
    Never pass test data here -- it would contaminate the evaluation.

    Returns: number of flows ingested
    """
    total = 0
    records = build_flow_batch(df)
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        run_batch_query(_FLOW_MERGE_QUERY, batch)
        total += len(batch)
    return total


def ingest_flows_batch(df: pd.DataFrame, batch_size: int = None):
    """
    DEPRECATED: Use ingest_flows() instead.

    This function has no train-only guard and may cause test-data leakage
    if called with evaluation data. ingest_flows() enforces the train-only
    contract via its docstring and call-site conventions.

    For each flow, creates:
    1. Source Device node (MERGE on IP)
    2. Destination Device node (MERGE on IP)
    3. Flow node
    4. AttackType node (MERGE)
    5. Port nodes (MERGE)
    6. INITIATES, TARGETS, CLASSIFIED_AS, USES, ON_PORT relationships
    """
    import warnings
    warnings.warn(
        "ingest_flows_batch() is deprecated and has no train-only guard. "
        "Use ingest_flows() instead to avoid accidental test-data leakage.",
        DeprecationWarning,
        stacklevel=2,
    )
    batch_size = batch_size or NEO4J_BATCH_SIZE
    total_rows = len(df)
    n_batches = math.ceil(total_rows / batch_size)

    logger.info(f"Ingesting {total_rows:,} flows in {n_batches} batches (size={batch_size})")

    # Replace NaN with None for Neo4j compatibility
    df = df.fillna({
        "duration": 0.0,
        "orig_bytes": 0,
        "resp_bytes": 0,
        "orig_pkts": 0,
        "resp_pkts": 0,
        "service": "unknown",
        "conn_state": "OTH",
        "protocol": "TCP",
        "attack_category": "Unknown",
    })

    # Main ingestion query " creates all nodes and relationships in one pass
    ingest_query = """
    UNWIND $batch AS row

    // Source Device
    MERGE (src:Device {ip: row.src_ip})
    ON CREATE SET src.first_seen = row.timestamp, src.dataset = row.dataset
    SET src.last_seen = CASE WHEN row.timestamp > coalesce(src.last_seen, 0)
                             THEN row.timestamp ELSE src.last_seen END

    // Destination Device
    MERGE (dst:Device {ip: row.dst_ip})
    ON CREATE SET dst.first_seen = row.timestamp, dst.dataset = row.dataset
    SET dst.last_seen = CASE WHEN row.timestamp > coalesce(dst.last_seen, 0)
                             THEN row.timestamp ELSE dst.last_seen END

    // Flow Node
    CREATE (f:Flow {
        uid: row.uid,
        timestamp: toFloat(row.timestamp),
        duration: toFloat(row.duration),
        orig_bytes: toInteger(row.orig_bytes),
        resp_bytes: toInteger(row.resp_bytes),
        orig_pkts: toInteger(row.orig_pkts),
        resp_pkts: toInteger(row.resp_pkts),
        conn_state: row.conn_state,
        service: row.service,
        label: row.label,
        dataset: row.dataset
    })

    // Relationships: Device ' Flow ' Device
    CREATE (src)-[:INITIATES]->(f)
    CREATE (f)-[:TARGETS]->(dst)

    // Protocol
    MERGE (proto:Protocol {name: row.protocol})
    CREATE (f)-[:USES]->(proto)

    // Attack Type
    MERGE (attack:AttackType {name: row.label})
    ON CREATE SET attack.description = row.label + ' attack',
                  attack.count = 0
    SET attack.count = coalesce(attack.count, 0) + 1
    CREATE (f)-[:CLASSIFIED_AS]->(attack)

    // Attack Category relationship
    WITH attack, row
    MATCH (cat:AttackCategory {name: row.attack_category})
    MERGE (attack)-[:BELONGS_TO]->(cat)
    """

    total_summary = {
        "nodes_created": 0,
        "relationships_created": 0,
        "properties_set": 0,
    }

    for i in tqdm(range(n_batches), desc="Ingesting flows"):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, total_rows)
        batch_df = df.iloc[start_idx:end_idx]

        # Convert batch to list of dicts for Neo4j
        batch_data = batch_df.to_dict("records")

        try:
            summary = run_batch_query(ingest_query, batch_data)
            for key in total_summary:
                total_summary[key] += summary.get(key, 0)
        except Exception as e:
            logger.error(f"Batch {i} failed: {e}")
            # Try individual rows for this batch
            for record in batch_data:
                try:
                    run_batch_query(ingest_query, [record])
                except Exception as inner_e:
                    logger.warning(f"  Skipping flow {record.get('uid', '?')}: {inner_e}")

    logger.info(f"\nIngestion Complete:")
    logger.info(f"  Nodes created:         {total_summary['nodes_created']:,}")
    logger.info(f"  Relationships created: {total_summary['relationships_created']:,}")
    logger.info(f"  Properties set:        {total_summary['properties_set']:,}")

    return total_summary


def create_port_nodes(df: pd.DataFrame):
    """Create Port nodes for unique destination ports."""
    unique_ports = df["dst_port"].dropna().unique()
    port_data = []
    for port in unique_ports:
        port = int(port)
        port_data.append({
            "number": port,
            "service_name": WELL_KNOWN_PORTS.get(port, f"port-{port}"),
        })

    query = """
    UNWIND $batch AS row
    MERGE (p:Port {number: row.number})
    SET p.service_name = row.service_name
    """

    # Batch port creation
    batch_size = 1000
    for i in range(0, len(port_data), batch_size):
        run_batch_query(query, port_data[i:i + batch_size])

    logger.info(f"Created {len(port_data)} Port nodes")


def create_communication_edges():
    """
    Create aggregated COMMUNICATES_WITH relationships between devices.
    This aggregates individual flows into a summary edge.
    """
    query = """
    MATCH (src:Device)-[:INITIATES]->(f:Flow)-[:TARGETS]->(dst:Device)
    WITH src, dst,
         count(f) as flow_count,
         sum(f.orig_bytes + f.resp_bytes) as total_bytes,
         collect(DISTINCT f.label) as attack_types
    MERGE (src)-[r:COMMUNICATES_WITH]->(dst)
    SET r.flow_count = flow_count,
        r.total_bytes = total_bytes,
        r.attack_types = attack_types
    """
    logger.info("Creating aggregated COMMUNICATES_WITH edges...")
    summary = run_write_query(query)
    logger.info(f"  Created {summary.get('relationships_created', 0)} COMMUNICATES_WITH edges")


def update_device_roles():
    """Update Device role property based on their behavior in flows."""
    query = """
    MATCH (d:Device)
    OPTIONAL MATCH (d)-[:INITIATES]->()
    WITH d, count(*) as initiated
    OPTIONAL MATCH ()-[:TARGETS]->(d)
    WITH d, initiated, count(*) as targeted
    SET d.role = CASE
        WHEN initiated > 0 AND targeted > 0 THEN 'both'
        WHEN initiated > 0 THEN 'source'
        WHEN targeted > 0 THEN 'target'
        ELSE 'unknown'
    END,
    d.flow_count = initiated + targeted
    """
    run_write_query(query)
    logger.info("Updated Device roles")


def link_devices_to_datasets():
    """Create IN_DATASET relationships."""
    query = """
    MATCH (d:Device)
    WHERE d.dataset IS NOT NULL
    MATCH (ds:Dataset {name: d.dataset})
    MERGE (d)-[:IN_DATASET]->(ds)
    """
    run_write_query(query)
    logger.info("Linked Devices to Datasets")


def ingest_full_pipeline(data_file: Path = None, use_sample: bool = True):
    """
    Run the complete flow ingestion pipeline.

    Args:
        data_file: Path to CSV file to ingest
        use_sample: If True and no data_file given, use dev sample
    """
    if data_file is None:
        if use_sample:
            data_file = DATA_SAMPLES_DIR / "dev_sample.csv"
        else:
            data_file = DATA_PROCESSED_DIR / "unified_features.csv"

    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        logger.info("Run Stage 2 first to create processed data files")
        return False

    if not verify_connectivity():
        logger.error("Neo4j not available. Start Neo4j first.")
        return False

    logger.info("=" * 60)
    logger.info("  Stage 3: Knowledge Graph Ingestion")
    logger.info("=" * 60)
    logger.info(f"  Data file: {data_file}")

    # Load data
    df = pd.read_csv(data_file, low_memory=False)
    logger.info(f"  Loaded {len(df):,} flows")

    # Step 1: Create reference nodes
    create_dataset_nodes()
    create_attack_category_nodes()
    create_protocol_nodes()

    # Step 2: Create port nodes
    create_port_nodes(df)

    # Step 3: Ingest flows (creates Devices, Flows, relationships)
    ingest_flows_batch(df)

    # Step 4: Create aggregated edges
    create_communication_edges()

    # Step 5: Update device metadata
    update_device_roles()
    link_devices_to_datasets()

    # Print final stats
    print_database_stats()

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest flows into Neo4j KG")
    parser.add_argument("--file", type=str, help="Path to CSV file to ingest")
    parser.add_argument("--full", action="store_true", help="Use full dataset instead of sample")
    args = parser.parse_args()

    data_file = Path(args.file) if args.file else None
    ingest_full_pipeline(data_file=data_file, use_sample=not args.full)
