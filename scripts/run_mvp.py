#!/usr/bin/env python3
"""
MVP Demo: demonstrates the core contribution of the thesis.

Shows:
1. Data normalization (CICIoT2023 sample)
2. Neo4j graph construction
3. node2vec + sentence-transformer embeddings
4. Dual retrieval (Cypher + vector)
5. LLM explanation for a specific attack
6. Grounding ratio
7. XGBoost baseline comparison

Run with: python scripts/run_mvp.py --sample-size 5000
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser(description="IoT CTI Pipeline MVP Demo")
    parser.add_argument("--ciciot-dir", type=Path, default=Path("data/raw/ciciot2023"))
    parser.add_argument("--sample-size", type=int, default=5000)
    parser.add_argument("--skip-neo4j", action="store_true", help="Skip graph stages (for offline demo)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  IoT Cyber Threat Intelligence Pipeline -- MVP Demo")
    print("=" * 60)

    # Stage 1: Data
    print("\n[Stage 1] Loading and normalizing flows...")
    from src.services.feature_extraction.extract_ciciot import extract_ciciot
    if not args.ciciot_dir.exists():
        print(f"ERROR: CICIoT directory not found: {args.ciciot_dir}")
        print("Download CICIoT2023 from: https://www.unb.ca/cic/datasets/iotdataset-2023.html")
        sys.exit(1)

    try:
        splits = extract_ciciot(args.ciciot_dir)
    except Exception as exc:
        print(f"ERROR: Failed to load CICIoT2023 data from {args.ciciot_dir}: {exc}")
        sys.exit(1)

    train_df = splits["train"].head(int(args.sample_size * 0.8))
    test_df = splits["test"].head(int(args.sample_size * 0.2))
    print(f"  Train: {len(train_df)} flows | Test: {len(test_df)} flows")
    print(f"  Attack classes: {sorted(train_df['label'].unique())}")

    # Stage 2: Baseline
    print("\n[Stage 2] Training XGBoost baseline...")
    from src.services.evaluation.baseline import train_xgboost_baseline
    baseline = train_xgboost_baseline(train_df, test_df)
    print(f"  XGBoost Macro F1: {baseline.macro_f1}")
    print(f"  XGBoost AUC-ROC:  {baseline.auc_roc}")

    # Track which stages ran and their key results for the report
    stages_run = ["Stage 1: Data normalisation", "Stage 2: XGBoost baseline"]
    grounding_ratio = None
    explanation_excerpt = None

    neo4j_available = False
    if not args.skip_neo4j:
        # Stage 3: Graph
        print("\n[Stage 3] Ingesting flows into Neo4j...")
        from src.services.knowledge_graph.schema_setup import setup_full_schema
        from src.services.knowledge_graph.ingest_flows import ingest_flows
        from src.services.knowledge_graph.neo4j_connection import verify_connectivity
        if not verify_connectivity():
            print("  WARNING: Neo4j not available. Skipping graph stages (4-6).")
        else:
            neo4j_available = True
            setup_full_schema()
            count = ingest_flows(train_df, batch_size=500)
            print(f"  Ingested {count} flows")
            stages_run.append("Stage 3: Neo4j ingestion")

    if neo4j_available:
        # Stage 4: Embeddings
        print("\n[Stage 4] Generating embeddings...")
        from src.services.graph_embeddings.embeddings import generate_all_embeddings
        generate_all_embeddings()
        print("  Embeddings complete")
        stages_run.append("Stage 4: Embeddings")

        # Stage 5: Retrieval demo
        print("\n[Stage 5] Retrieval demo -- attack: DDoS-TCP_Flood")
        from src.services.graphrag.retrievers import CypherRetriever, VectorGraphRetriever
        cypher = CypherRetriever()
        vector = VectorGraphRetriever()
        cypher_ctx = cypher.retrieve("DDoS TCP flood attack devices")
        vector_ctx = vector.retrieve("DDoS TCP flood", search_type="attack")
        print(f"  Cypher retrieved: {len(cypher_ctx.get('results', []))} items")
        print(f"  Vector retrieved: {len(vector_ctx.get('results', []))} items")
        stages_run.append("Stage 5: Dual retrieval")

        # Stage 6: LLM Explanation
        print("\n[Stage 6] Generating LLM explanation...")
        from src.services.threat_explanation.explainer import ThreatExplainer
        from src.services.threat_explanation.grounding import check_grounding
        explainer = ThreatExplainer()
        result = explainer.explain_attack("DDoS-TCP_Flood")
        grounding = check_grounding(result["analysis"], vector_ctx.get("context_text", ""))
        grounding_ratio = grounding.grounding_ratio
        explanation_excerpt = result["analysis"][:500]
        print(f"  Grounding ratio: {grounding_ratio}")
        print(f"  Ungrounded entities: {grounding.ungrounded_entities[:5]}")
        print(f"\n--- Explanation excerpt ---")
        print(explanation_excerpt)
        stages_run.append("Stage 6: LLM explanation + grounding")

    print("\n" + "=" * 60)
    print("  MVP Demo Complete")
    print(f"  Baseline Macro F1: {baseline.macro_f1}")
    print("=" * 60)

    # Write Markdown report
    report_path = Path("data/eval/mvp_demo_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# MVP Demo Report",
        "",
        f"**Generated:** {timestamp}",
        "",
        "## Stages Run",
        "",
    ]
    for stage in stages_run:
        lines.append(f"- {stage}")
    lines += [
        "",
        "## Key Metrics",
        "",
        f"- **Train flows:** {len(train_df)}",
        f"- **Test flows:** {len(test_df)}",
        f"- **Baseline Macro F1:** {baseline.macro_f1}",
        f"- **Baseline AUC-ROC:** {baseline.auc_roc}",
    ]
    if grounding_ratio is not None:
        lines.append(f"- **Grounding ratio:** {grounding_ratio}")
    if explanation_excerpt is not None:
        lines += [
            "",
            "## Explanation Excerpt",
            "",
            "```",
            explanation_excerpt,
            "```",
        ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n  Report saved to: {report_path}")


if __name__ == "__main__":
    main()
