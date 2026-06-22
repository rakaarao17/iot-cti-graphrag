import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import logger
from src.services.knowledge_graph.neo4j_connection import run_query_single, print_database_stats

def finish_stage3_batched():
    logger.info("Finishing Stage 3: Creating COMMUNICATES_WITH edges in python batches...")
    
    # 1. COMMUNICATES_WITH
    edge_query = """
    MATCH (src:Device)-[:INITIATES]->(f:Flow)-[:TARGETS]->(dst:Device)
    WHERE NOT (src)-[:COMMUNICATES_WITH]->(dst)
    WITH src, dst LIMIT 1000
    MATCH (src)-[:INITIATES]->(f:Flow)-[:TARGETS]->(dst)
    WITH src, dst,
         count(f) as flow_count,
         sum(f.orig_bytes + f.resp_bytes) as total_bytes,
         collect(DISTINCT f.label) as attack_types
    MERGE (src)-[r:COMMUNICATES_WITH]->(dst)
    SET r.flow_count = flow_count,
        r.total_bytes = total_bytes,
        r.attack_types = attack_types
    RETURN count(r) as processed
    """
    
    total_edges = 0
    while True:
        try:
            res = run_query_single(edge_query)
            processed = res['processed'] if res else 0
            total_edges += processed
            if processed == 0:
                break
            logger.info(f"  Created {total_edges} COMMUNICATES_WITH edges so far...")
        except Exception as e:
            logger.error(f"Error in edge batch: {e}")
            break
            
    # 2. IN_DATASET
    logger.info("Linking devices to datasets in batches...")
    dataset_query = """
    MATCH (d:Device)
    WHERE d.dataset IS NOT NULL AND NOT (d)-[:IN_DATASET]->()
    WITH d LIMIT 10000
    MATCH (ds:Dataset {name: d.dataset})
    MERGE (d)-[:IN_DATASET]->(ds)
    RETURN count(d) as processed
    """
    
    total_datasets = 0
    while True:
        try:
            res = run_query_single(dataset_query)
            processed = res['processed'] if res else 0
            total_datasets += processed
            if processed == 0:
                break
            logger.info(f"  Linked {total_datasets} devices so far...")
        except Exception as e:
            logger.error(f"Error in dataset batch: {e}")
            break

    print_database_stats()
    logger.info("Stage 3 completely finished!")

if __name__ == "__main__":
    finish_stage3_batched()
