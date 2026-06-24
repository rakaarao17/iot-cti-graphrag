"""
Master Pipeline Orchestrator.

Runs all 6 stages of the GraphRAG IoT Cyber Threat Intelligence pipeline
sequentially or individually via CLI.
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import logger, print_config


def run_stage_1():
    """Stage 1: Generate sample data (or download real datasets)."""
    logger.info("\n" + "â•" * 70)
    logger.info("  STAGE 1: Dataset Acquisition")
    logger.info("â•" * 70)

    from src.services.data_acquisition.download_iot23 import download_all_scenarios
    from src.services.data_acquisition.download_ciciot import generate_manual_instructions

    logger.info("Downloading genuine IoT-23 data scenarios (no synthetic data)...")
    download_all_scenarios(max_scenarios=2)  # Downloading 2 real scenarios to save time, but it's genuine data
    
    logger.info("For genuine CICIoT2023 data, manual download is required:")
    generate_manual_instructions()

    logger.info("Stage 1 Complete âœ“")


def run_stage_2():
    """Stage 2: Feature extraction and engineering."""
    logger.info("\n" + "â•" * 70)
    logger.info("  STAGE 2: Feature Extraction & Engineering")
    logger.info("â•" * 70)

    from src.services.feature_extraction.extract_iot23 import extract_iot23
    from src.services.feature_extraction.extract_ciciot import extract_ciciot
    from src.services.feature_extraction.feature_engineering import combine_datasets
    from src.services.feature_extraction.sampler import create_dev_samples

    extract_iot23()
    extract_ciciot()
    combine_datasets()
    create_dev_samples()

    logger.info("Stage 2 Complete âœ“")


def run_stage_3():
    """Stage 3: Knowledge Graph construction in Neo4j."""
    logger.info("\n" + "â•" * 70)
    logger.info("  STAGE 3: Knowledge Graph Construction")
    logger.info("â•" * 70)

    from src.services.knowledge_graph.schema_setup import setup_full_schema
    from src.services.knowledge_graph.ingest_flows import ingest_full_pipeline
    from src.services.knowledge_graph.enrich_mitre import enrich_with_mitre

    if not setup_full_schema():
        logger.error("Schema setup failed. Is Neo4j running?")
        return False

    ingest_full_pipeline(use_sample=False)
    enrich_with_mitre()

    logger.info("Stage 3 Complete âœ“")
    return True


def run_stage_4():
    """Stage 4: Graph queries and embeddings."""
    logger.info("\n" + "â•" * 70)
    logger.info("  STAGE 4: Graph Embeddings")
    logger.info("â•" * 70)

    from src.services.graph_embeddings.graph_features import compute_all_graph_features
    from src.services.graph_embeddings.embeddings import generate_all_embeddings

    compute_all_graph_features()
    generate_all_embeddings()

    logger.info("Stage 4 Complete âœ“")


def run_stage_5():
    """Stage 5: GraphRAG setup and verification."""
    logger.info("\n" + "â•" * 70)
    logger.info("  STAGE 5: GraphRAG Setup")
    logger.info("â•" * 70)

    from src.services.graphrag.vector_store import verify_vector_indexes, get_embedding_stats

    verify_vector_indexes()
    stats = get_embedding_stats()
    for name, info in stats.items():
        logger.info(f"  {name}: {info['embedded_nodes']} nodes embedded")

    logger.info("Stage 5 Complete âœ“")


def run_stage_6():
    """Stage 6: Test threat explanation."""
    logger.info("\n" + "â•" * 70)
    logger.info("  STAGE 6: Threat Explanation Test")
    logger.info("â•" * 70)

    from src.services.graphrag.rag_pipeline import GraphRAGPipeline

    pipeline = GraphRAGPipeline()

    test_questions = [
        "What are the most dangerous devices in the IoT network?",
        "Explain the DDoS attacks observed in the dataset",
        "How do the attack patterns compare between IoT-23 and CICIoT2023?",
    ]

    for question in test_questions:
        logger.info(f"\n  Question: {question}")
        try:
            result = pipeline.query(question, retrieval_method="auto")
            # Print first 500 chars of answer
            answer_preview = result["answer"][:500]
            logger.info(f"  Answer: {answer_preview}...")
        except Exception as e:
            logger.warning(f"  Error: {e}")

    logger.info("Stage 6 Complete âœ“")


def run_all_stages():
    """Run the complete pipeline."""
    start_time = time.time()

    print_config()

    stages = [
        (1, "Dataset Acquisition", run_stage_1),
        (2, "Feature Extraction", run_stage_2),
        (3, "Knowledge Graph", run_stage_3),
        (4, "Graph Embeddings", run_stage_4),
        (5, "GraphRAG Setup", run_stage_5),
        (6, "Threat Explanation", run_stage_6),
    ]

    results = {}
    for num, name, func in stages:
        stage_start = time.time()
        try:
            logger.info(f"\n{'â”' * 70}")
            logger.info(f"  Starting Stage {num}: {name}")
            logger.info(f"{'â”' * 70}")
            result = func()
            results[num] = "âœ“ Success"
        except Exception as e:
            logger.error(f"Stage {num} failed: {e}", exc_info=True)
            results[num] = f"âœ— Failed: {e}"
            if num <= 3:  # Critical stages
                logger.error("Critical stage failed. Stopping pipeline.")
                break
        finally:
            elapsed = time.time() - stage_start
            logger.info(f"  Stage {num} elapsed: {elapsed:.1f}s")

    # Pipeline summary
    total_elapsed = time.time() - start_time
    print("\n" + "-" * 70)
    print("  PIPELINE EXECUTION SUMMARY")
    print("-" * 70)
    for num, status in results.items():
        print(f"  Stage {num}: {status}")
    print(f"\n  Total time: {total_elapsed:.1f}s")
    print("-" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="GraphRAG IoT Cyber Threat Intelligence Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_pipeline.py --all             Run complete pipeline
  python scripts/run_pipeline.py --stage 1         Run Stage 1 only
  python scripts/run_pipeline.py --stage 3         Run Stage 3 (Neo4j)
  python scripts/run_pipeline.py --interactive     Start interactive analyst
        """,
    )
    parser.add_argument("--all", action="store_true", help="Run all 6 stages")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4, 5, 6], help="Run a specific stage")
    parser.add_argument("--interactive", action="store_true", help="Start interactive threat analysis")
    parser.add_argument("--auto-demo", action="store_true", help="Run automated demo queries")
    parser.add_argument("--config", action="store_true", help="Print configuration and exit")

    args = parser.parse_args()

    if args.config:
        print_config()
    elif args.interactive:
        from src.cli.main import interactive_session
        interactive_session(auto_demo=args.auto_demo)
    elif args.stage:
        stage_funcs = {
            1: run_stage_1, 2: run_stage_2, 3: run_stage_3,
            4: run_stage_4, 5: run_stage_5, 6: run_stage_6,
        }
        stage_funcs[args.stage]()
    elif args.all:
        run_all_stages()
    else:
        parser.print_help()
        print("\n  Tip: Use --all to run the complete pipeline")


if __name__ == "__main__":
    main()
