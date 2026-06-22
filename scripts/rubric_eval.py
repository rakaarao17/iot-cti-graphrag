#!/usr/bin/env python3
"""
Human rubric evaluation for the IoT CTI GraphRAG ablation study.

Presents 20 selected queries one at a time. For each query, shows the
context retrieved by CYPHER_ONLY, VECTOR_ONLY, and COMBINED. You score
each condition 1-5 for relevance. Scores are appended to the output CSV
after every query so progress is never lost.

Usage:
    python scripts/rubric_eval.py
    python scripts/rubric_eval.py --output data/eval/rubric_scores.csv
    python scripts/rubric_eval.py --resume   # skip already-scored queries
"""

import argparse
import csv
import json
import os
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ABLATION_FILE = ROOT / "data" / "eval" / "ablation_results.json"
DEFAULT_OUTPUT = ROOT / "data" / "eval" / "rubric_scores.csv"

RUBRIC_QUERIES = [
    "q001", "q023",         # device_lookup
    "q002", "q020",         # relationship_traversal
    "q003", "q018", "q032", # mitre_lookup
    "q004", "q017", "q035", # attack_description
    "q005", "q015", "q024", # aggregation
    "q006", "q016",         # device_ranking
    "q007", "q026",         # mitre_tactic
    "q009", "q034",         # attack_device_join
    "q011",                  # dataset_comparison
]

SCORE_GUIDE = """
Relevance scoring rubric (1-5):
  5 - Directly answers the query; entities and details are exactly right
  4 - Mostly relevant; answers the core question with minor gaps
  3 - Partially relevant; some useful info but key details missing or off-topic
  2 - Marginally relevant; mostly off-topic but contains something related
  1 - Not relevant; context does not help answer the query at all
"""

CONDITIONS = ["cypher_only", "vector_only", "combined"]
WRAP_WIDTH = 90
CONTEXT_PREVIEW = 60  # lines of context to show per condition before truncating


def load_ablation(path: Path) -> dict:
    """Return {(query_id, condition): record} from ablation_results.json."""
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    index = {}
    for r in records:
        index[(r["query_id"], r["condition"])] = r
    return index


def load_scored_ids(output_path: Path) -> set:
    """Return set of query_ids already in the output CSV."""
    if not output_path.exists():
        return set()
    with open(output_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["query_id"] for row in reader}


def write_header(output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "query_id", "query_text", "retrieval_type",
            "cypher_only_score", "vector_only_score", "combined_score",
            "cypher_only_notes", "vector_only_notes", "combined_notes",
            "overall_notes",
        ])


def append_row(output_path: Path, row: dict) -> None:
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "query_id", "query_text", "retrieval_type",
            "cypher_only_score", "vector_only_score", "combined_score",
            "cypher_only_notes", "vector_only_notes", "combined_notes",
            "overall_notes",
        ])
        writer.writerow(row)


def display_context(condition: str, record: dict | None) -> None:
    if record is None:
        print(f"\n  [{condition.upper()}]  -- no data --")
        return

    result_count = len(record.get("results", []))
    latency = record.get("latency_ms", "?")
    context = record.get("context_text", "(no context)")
    lines = context.splitlines()

    print(f"\n{'=' * WRAP_WIDTH}")
    print(f"  CONDITION: {condition.upper()}")
    print(f"  Results: {result_count}  |  Latency: {latency} ms")
    print(f"{'=' * WRAP_WIDTH}")

    if len(lines) > CONTEXT_PREVIEW:
        shown = lines[:CONTEXT_PREVIEW]
        print("\n".join(shown))
        print(f"\n  ... [{len(lines) - CONTEXT_PREVIEW} more lines truncated] ...")
    else:
        print("\n".join(lines))


def get_score(condition: str) -> tuple[int, str]:
    while True:
        raw = input(f"\n  Score for {condition.upper()} (1-5, or q to quit): ").strip()
        if raw.lower() == "q":
            print("Quitting. Progress saved.")
            sys.exit(0)
        if raw in {"1", "2", "3", "4", "5"}:
            score = int(raw)
            notes = input(f"  Notes for {condition.upper()} (optional, press Enter to skip): ").strip()
            return score, notes
        print("  Enter 1-5 only.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Human rubric evaluation for ablation study")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path")
    parser.add_argument("--resume", action="store_true", help="Skip already-scored queries")
    args = parser.parse_args()

    output_path = Path(args.output)
    ablation = load_ablation(ABLATION_FILE)

    already_scored: set = set()
    if args.resume and output_path.exists():
        already_scored = load_scored_ids(output_path)
        print(f"[RESUME] Found {len(already_scored)} already-scored queries, skipping them.")

    if not output_path.exists():
        write_header(output_path)

    print(SCORE_GUIDE)
    print(f"Evaluating {len(RUBRIC_QUERIES)} queries. Output: {output_path}")
    print("Type 'q' at any score prompt to quit and save progress.\n")

    remaining = [qid for qid in RUBRIC_QUERIES if qid not in already_scored]
    total = len(remaining)

    for i, qid in enumerate(remaining, 1):
        cypher_rec = ablation.get((qid, "cypher_only"))
        vector_rec = ablation.get((qid, "vector_only"))
        combined_rec = ablation.get((qid, "combined"))

        query_text = (cypher_rec or vector_rec or combined_rec or {}).get("query", "?")
        retrieval_type = "unknown"
        for r in [cypher_rec, vector_rec, combined_rec]:
            if r:
                retrieval_type = r.get("retrieval_type", "unknown")
                break

        os.system("cls" if os.name == "nt" else "clear")
        print(f"\n{'#' * WRAP_WIDTH}")
        print(f"  QUERY {i}/{total}  |  ID: {qid}  |  Type: {retrieval_type}")
        print(f"  \"{query_text}\"")
        print(f"{'#' * WRAP_WIDTH}")

        display_context("cypher_only", cypher_rec)
        display_context("vector_only", vector_rec)
        display_context("combined", combined_rec)

        print(f"\n{'-' * WRAP_WIDTH}")
        print("  SCORE EACH CONDITION:")
        print(SCORE_GUIDE)

        c_score, c_notes = get_score("cypher_only")
        v_score, v_notes = get_score("vector_only")
        m_score, m_notes = get_score("combined")
        overall = input("\n  Overall notes for this query (optional): ").strip()

        append_row(output_path, {
            "query_id": qid,
            "query_text": query_text,
            "retrieval_type": retrieval_type,
            "cypher_only_score": c_score,
            "vector_only_score": v_score,
            "combined_score": m_score,
            "cypher_only_notes": c_notes,
            "vector_only_notes": v_notes,
            "combined_notes": m_notes,
            "overall_notes": overall,
        })
        print(f"  [SAVED] {qid} scored.")

    print(f"\n[DONE] All {total} queries scored. Results in: {output_path}")


if __name__ == "__main__":
    main()
