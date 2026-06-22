#!/usr/bin/env python3
"""
Session 5 fix: rebuild vector indexes at 384-dim and re-embed metadata nodes.

Old Gemini-era indexes were created at 768-dim. sentence-transformers produces
384-dim vectors, so vector search silently returns nothing. This script:
  1. Checks current embedding dimensions per node type
  2. Drops all vector indexes (even if dimension looks right -- guarantees clean slate)
  3. Recreates them at 384-dim via schema_setup
  4. Re-embeds AttackType and MITRETechnique nodes (always small, fast)
  5. Re-embeds Device nodes only if their stored embeddings are not 384-dim
  6. Waits for indexes to go ONLINE
  7. Smoke-tests a vector query against each index

Usage:
    python scripts/fix_vector_indexes.py
    python scripts/fix_vector_indexes.py --skip-devices   # skip re-embedding devices
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import EMBEDDING_DIMENSION, logger
from src.services.knowledge_graph.neo4j_connection import (
    run_query, run_write_query, run_batch_query, verify_connectivity,
)


TARGET_DIM = EMBEDDING_DIMENSION  # 384

VECTOR_INDEX_NAMES = [
    "device_embedding",
    "attack_embedding",
    "mitre_embedding",
    "flow_embedding",
]


# -- Step 1: diagnose ---------------------------------------------------------

def check_embedding_dims() -> dict:
    """Return actual embedding dimension stored per node label."""
    checks = {
        "Device":         "MATCH (n:Device) WHERE n.embedding IS NOT NULL RETURN size(n.embedding) AS dim LIMIT 1",
        "AttackType":     "MATCH (n:AttackType) WHERE n.embedding IS NOT NULL RETURN size(n.embedding) AS dim LIMIT 1",
        "MITRETechnique": "MATCH (n:MITRETechnique) WHERE n.embedding IS NOT NULL RETURN size(n.embedding) AS dim LIMIT 1",
    }
    dims = {}
    for label, q in checks.items():
        result = run_query(q)
        dims[label] = result[0]["dim"] if result else None
    return dims


def check_existing_indexes() -> dict:
    """Return existing vector index names with their configured dimensions."""
    rows = run_query("SHOW INDEXES WHERE type = 'VECTOR'")
    out = {}
    for r in rows:
        name = r.get("name", "")
        options = r.get("options", {}) or {}
        idx_cfg = options.get("indexConfig", {}) or {}
        dim = idx_cfg.get("vector.dimensions")
        out[name] = {"state": r.get("state"), "dim": dim}
    return out


# -- Step 2: drop -------------------------------------------------------------

def drop_vector_indexes():
    """Drop all known vector indexes unconditionally."""
    for name in VECTOR_INDEX_NAMES:
        try:
            run_write_query(f"DROP INDEX {name} IF EXISTS")
            logger.info(f"  Dropped index: {name}")
        except Exception as e:
            logger.warning(f"  Could not drop {name}: {e}")


# -- Step 3: recreate ---------------------------------------------------------

def create_vector_indexes():
    """Create fresh vector indexes at TARGET_DIM."""
    definitions = [
        ("device_embedding",  "Device",         "embedding"),
        ("attack_embedding",  "AttackType",      "embedding"),
        ("mitre_embedding",   "MITRETechnique",  "embedding"),
        ("flow_embedding",    "Flow",            "embedding"),
    ]
    for name, label, prop in definitions:
        cypher = f"""
        CREATE VECTOR INDEX {name} IF NOT EXISTS
        FOR (n:{label}) ON (n.{prop})
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {TARGET_DIM},
            `vector.similarity_function`: 'cosine'
        }}}}
        """
        try:
            run_write_query(cypher)
            logger.info(f"  Created index: {name} ({label}.{prop}, dim={TARGET_DIM})")
        except Exception as e:
            logger.error(f"  Failed to create {name}: {e}")


def wait_for_indexes_online(timeout_s: int = 60):
    """Poll until all vector indexes report ONLINE, or timeout."""
    logger.info(f"Waiting for indexes to come ONLINE (timeout={timeout_s}s)...")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        rows = run_query("SHOW INDEXES WHERE type = 'VECTOR'")
        states = {r["name"]: r["state"] for r in rows}
        not_online = [n for n, s in states.items() if s != "ONLINE"]
        if not not_online:
            logger.info("  All vector indexes are ONLINE")
            return True
        logger.info(f"  Waiting on: {not_online}")
        time.sleep(3)
    logger.warning("Timed out waiting for indexes")
    return False


# -- Step 4 & 5: re-embed -----------------------------------------------------

def reembed_attack_types():
    from src.services.graph_embeddings.embeddings import embed_attack_type_nodes
    logger.info("Re-embedding AttackType nodes...")
    embed_attack_type_nodes()


def reembed_mitre_nodes():
    from src.services.graph_embeddings.embeddings import embed_mitre_nodes
    logger.info("Re-embedding MITRETechnique nodes...")
    embed_mitre_nodes()


def reembed_device_nodes_with_checkpoint():
    """
    Re-embed Device nodes at 384-dim, skipping any already at the right dimension.

    Safe to kill and restart at any time -- already-embedded devices are skipped
    on the next run. Progress is shown every 10,000 devices.
    """
    from src.services.graph_embeddings.text_embeddings import get_local_embeddings

    logger.info("Re-embedding Device nodes (checkpoint-safe, skips already-done)...")

    # Only fetch devices whose embedding is missing or wrong dimension
    query = f"""
    MATCH (d:Device)
    WHERE d.total_degree IS NOT NULL
      AND (d.embedding IS NULL OR size(d.embedding) <> {TARGET_DIM})
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

    if not devices:
        logger.info("  All Device nodes already at 384-dim. Nothing to do.")
        return

    logger.info(f"  {len(devices):,} devices need re-embedding (others already done)")

    batch_size = 500
    total_done = 0

    for i in range(0, len(devices), batch_size):
        batch = devices[i:i + batch_size]

        texts = []
        for d in batch:
            attacks = d.get("attacks", [])
            attack_str = ", ".join(attacks[:5]) if attacks else "none"
            mal_pct = (d.get("mal_ratio") or 0) * 100
            text = (
                f"IoT device at IP {d['ip']} from {d.get('dataset', 'unknown')} dataset. "
                f"Role: {d.get('role', 'unknown')}. "
                f"Network activity: {d.get('degree', 0)} total connections, "
                f"communicates with {d.get('peers', 0)} peers, "
                f"uses {d.get('ports', 0)} distinct services. "
                f"Threat profile: {mal_pct:.1f}% malicious traffic ratio. "
                f"Attack types observed: {attack_str}. "
                f"Total flows: {d.get('flow_count', 0)}."
            )
            texts.append(text)

        embeddings = get_local_embeddings(texts)

        batch_data = [
            {"ip": d["ip"], "embedding": emb, "text_description": text}
            for d, emb, text in zip(batch, embeddings, texts)
        ]

        run_batch_query(
            """
            UNWIND $batch AS row
            MATCH (dev:Device {ip: row.ip})
            SET dev.embedding = row.embedding,
                dev.text_description = row.text_description
            """,
            batch_data,
        )

        total_done += len(batch)
        if total_done % 10_000 == 0:
            pct = total_done / len(devices) * 100
            logger.info(f"  ...{total_done:,} / {len(devices):,} devices done ({pct:.1f}%)")


# -- Step 6: smoke test -------------------------------------------------------

def smoke_test_vector_retrieval():
    """
    Embed a test query and run a vector search against each index.
    Returns True if at least one result is returned from each indexed node type
    that has embeddings.
    """
    from src.services.graph_embeddings.text_embeddings import get_local_embeddings

    test_query = "DDoS attack on IoT device using TCP flood"
    logger.info(f"\nSmoke test query: '{test_query}'")

    embeddings = get_local_embeddings([test_query])
    if not embeddings:
        logger.error("Failed to generate query embedding")
        return False

    qvec = embeddings[0]
    logger.info(f"  Query embedding dim: {len(qvec)}")

    tests = [
        ("attack_embedding",  "AttackType"),
        ("device_embedding",  "Device"),
        ("mitre_embedding",   "MITRETechnique"),
    ]

    all_ok = True
    for index_name, label in tests:
        try:
            result = run_query(
                """
                CALL db.index.vector.queryNodes($idx, 3, $vec)
                YIELD node, score
                RETURN node, score
                """,
                {"idx": index_name, "vec": qvec},
            )
            if result:
                logger.info(f"  [OK] {index_name}: {len(result)} result(s), top score={result[0]['score']:.4f}")
            else:
                # No results might mean no nodes have embeddings yet for this label
                count_q = run_query(f"MATCH (n:{label}) WHERE n.embedding IS NOT NULL RETURN count(n) AS c")
                embedded = count_q[0]["c"] if count_q else 0
                if embedded == 0:
                    logger.warning(f"  [WARN] {index_name}: 0 results - no {label} nodes have embeddings")
                else:
                    logger.error(f"  [FAIL] {index_name}: 0 results but {embedded} nodes have embeddings - index dim mismatch?")
                    all_ok = False
        except Exception as e:
            logger.error(f"  [FAIL] {index_name}: query failed -- {e}")
            all_ok = False

    return all_ok


# -- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fix vector indexes and re-embed metadata nodes")
    parser.add_argument("--skip-devices", action="store_true",
                        help="Skip re-embedding Device nodes (use if devices are already at 384-dim)")
    parser.add_argument("--smoke-only", action="store_true",
                        help="Only run the smoke test, skip all fixes")
    args = parser.parse_args()

    print("=" * 65)
    print("  Session 5 Fix: Vector Index Rebuild")
    print("=" * 65)

    if not verify_connectivity():
        logger.error("Neo4j not reachable. Start Neo4j and retry.")
        sys.exit(1)

    if args.smoke_only:
        ok = smoke_test_vector_retrieval()
        sys.exit(0 if ok else 1)

    # -- 1. Diagnose current state ------------------------------------------
    print("\n[1/6] Diagnosing current state...")
    dims = check_embedding_dims()
    for label, dim in dims.items():
        status = "OK" if dim == TARGET_DIM else ("MISMATCH" if dim else "not embedded")
        print(f"  {label}: stored dim={dim}  [{status}]")

    existing = check_existing_indexes()
    print(f"\n  Vector indexes in Neo4j:")
    for name, info in existing.items():
        dim_ok = "OK" if info["dim"] == TARGET_DIM else f"MISMATCH dim={info['dim']}"
        print(f"    {name}: state={info['state']}  {dim_ok}")

    # -- 2. Drop old indexes ------------------------------------------------
    print("\n[2/6] Dropping existing vector indexes...")
    drop_vector_indexes()

    # -- 3. Recreate at 384-dim ---------------------------------------------
    print(f"\n[3/6] Creating vector indexes at dim={TARGET_DIM}...")
    create_vector_indexes()

    # -- 4. Re-embed metadata nodes -----------------------------------------
    print("\n[4/6] Re-embedding AttackType and MITRETechnique nodes...")
    reembed_attack_types()
    reembed_mitre_nodes()

    # -- 5. Conditionally re-embed devices ---------------------------------
    if args.skip_devices:
        print("\n[5/6] Skipping Device re-embedding (--skip-devices)")
    else:
        print(f"\n[5/6] Re-embedding Device nodes (checkpoint-safe)...")
        reembed_device_nodes_with_checkpoint()

    # -- 6. Wait for indexes + smoke test ----------------------------------
    print("\n[6/6] Waiting for indexes to go ONLINE and running smoke test...")
    wait_for_indexes_online(timeout_s=90)
    ok = smoke_test_vector_retrieval()

    print("\n" + "=" * 65)
    if ok:
        print("  [OK] Vector indexes fixed. Ablation study should now work.")
        print("  Next: python scripts/evaluate.py")
    else:
        print("  [FAIL] Smoke test failed - check logs above.")
    print("=" * 65)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
