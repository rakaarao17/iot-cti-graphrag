#!/usr/bin/env python3
"""
Evaluation runner. Run after full pipeline is complete.

Usage:
    python scripts/evaluate.py --iot23-dir data/raw/iot23 --ciciot-dir data/raw/ciciot2023
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.feature_extraction.extract_iot23 import extract_iot23
from src.services.feature_extraction.extract_ciciot import extract_ciciot
from src.services.evaluation.baseline import train_xgboost_baseline
from src.services.evaluation.ablation import run_full_ablation
from src.services.evaluation.report import generate_evaluation_report


def main():
    parser = argparse.ArgumentParser(description="Run full evaluation pipeline")
    parser.add_argument("--iot23-dir", type=Path, default=Path("data/raw/iot23"))
    parser.add_argument("--ciciot-dir", type=Path, default=Path("data/raw/ciciot2023"))
    parser.add_argument("--queries", type=Path, default=Path("data/eval/curated_queries.json"))
    parser.add_argument("--output-dir", type=str, default="data/eval")
    parser.add_argument("--ablation-only", action="store_true",
                        help="Skip dataset loading and XGBoost baseline; run ablation study only")
    args = parser.parse_args()

    baseline = None

    if not args.ablation_only:
        print("=== Loading datasets ===")
        splits = {}
        if args.ciciot_dir.exists():
            try:
                splits["ciciot"] = extract_ciciot(args.ciciot_dir)
                print(f"CICIoT: {len(splits['ciciot']['train'])} train, {len(splits['ciciot']['test'])} test")
            except Exception as e:
                print(f"WARNING: CICIoT load failed ({e}) -- skipping")
        else:
            print(f"WARNING: CICIoT directory not found: {args.ciciot_dir}")

        if args.iot23_dir.exists():
            try:
                splits["iot23"] = extract_iot23(args.iot23_dir)
                print(f"IoT-23: {len(splits['iot23']['train'])} train, {len(splits['iot23']['test'])} test")
            except Exception as e:
                print(f"WARNING: IoT-23 load failed ({e}) -- skipping")
        else:
            print(f"WARNING: IoT-23 directory not found: {args.iot23_dir}")

        if splits:
            import pandas as pd
            train_df = pd.concat([s["train"] for s in splits.values()], ignore_index=True)
            test_df = pd.concat([s["test"] for s in splits.values()], ignore_index=True)
            print(f"\n=== XGBoost Baseline ===")
            baseline = train_xgboost_baseline(train_df, test_df)
            print(f"Macro F1: {baseline.macro_f1}")
        else:
            print("WARNING: No datasets loaded -- skipping XGBoost baseline")
    else:
        print("=== Ablation-only mode: skipping dataset loading and XGBoost baseline ===")

    print(f"\n=== Ablation Study ===")
    if args.queries.exists():
        with open(args.queries) as f:
            queries = json.load(f)
        ablation_results = run_full_ablation(queries, output_path=f"{args.output_dir}/ablation_results.json")
        print(f"Ablation complete: {len(ablation_results)} results")
    else:
        ablation_results = []
        print(f"WARNING: Queries file not found: {args.queries}")

    print(f"\n=== Generating Report ===")
    report = generate_evaluation_report(
        baseline_result=baseline,
        classification_result=None,
        ablation_results=ablation_results,
        grounding_results=[],
        output_dir=args.output_dir,
    )
    print(f"Report saved to {args.output_dir}/evaluation_report.json")
    print(f"Markdown saved to {args.output_dir}/evaluation_report.md")


if __name__ == "__main__":
    main()
