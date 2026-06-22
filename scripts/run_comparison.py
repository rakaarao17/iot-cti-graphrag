"""
CLI: Run 3-model LLM comparison against a benchmark query set.

Usage:
    python scripts/run_comparison.py \
        --benchmark data/eval/comparison_benchmark.json \
        --retrieval-cache data/eval/retrieval_cache.json \
        --output-dir data/eval

Models (all local Ollama):
    gemma4:e2b
    phi3:latest
    zeroday-phi3-ciciot-v2:latest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path when invoked as a script
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.adapters.llm_adapters import OllamaAdapter
from src.services.evaluation.llm_comparison import run_model_comparison
from src.services.evaluation.comparison_report import generate_comparison_report


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALL_MODELS = [
    "gemma4:e2b",
    "phi3:latest",
    "zeroday-phi3-ciciot-v2:latest",
]

_MODEL_ALIASES: dict[str, str] = {
    "gemma":  "gemma4:e2b",
    "phi3":   "phi3:latest",
    "zeroday": "zeroday-phi3-ciciot-v2:latest",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> object:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_models(requested: list[str] | None) -> list[str]:
    """Map CLI aliases/full names to canonical model names."""
    if not requested:
        return list(_ALL_MODELS)
    resolved = []
    for r in requested:
        resolvedname = _MODEL_ALIASES.get(r, r)
        if resolvedname == r and r not in _MODEL_ALIASES:
            print(f"[WARN] Unknown model alias '{r}' -- passing through as-is", file=sys.stderr)
        resolved.append(resolvedname)
    return resolved


def _merge_context(
    queries: list[dict],
    retrieval_cache: dict[str, str],
) -> list[dict]:
    """Attach 'context' from cache; skip queries with no entry (with warning)."""
    merged = []
    for q in queries:
        qid = q.get("id", q.get("query_id", ""))
        if qid not in retrieval_cache:
            print(f"[WARN] No retrieval cache entry for query '{qid}' -- skipping.", file=sys.stderr)
            continue
        merged.append({**q, "id": qid, "context": retrieval_cache[qid]})
    return merged


def _print_summary(results) -> None:
    """Print a summary table to stdout."""
    sep = "-" * 80
    print(sep)
    print(f"{'Query ID':<20} {'Model':<40} {'Grounding':>10} {'Error'}")
    print(sep)
    for r in results:
        for model_name, response in r.responses.items():
            gr = r.grounding.get(model_name)
            ratio = f"{gr.grounding_ratio:.2f}" if gr else "N/A"
            err = response.error or ""
            truncated_err = err[:40] + "..." if len(err) > 40 else err
            print(f"{r.query_id:<20} {model_name:<40} {ratio:>10}  {truncated_err}")
    print(sep)
    print(f"Total queries: {len(results)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run 3-model LLM comparison for IoT cybersecurity queries."
    )
    p.add_argument(
        "--benchmark",
        required=True,
        metavar="PATH",
        help="Path to comparison_benchmark.json",
    )
    p.add_argument(
        "--retrieval-cache",
        required=True,
        metavar="PATH",
        help="Path to retrieval_cache.json (query_id -> context_text)",
    )
    p.add_argument(
        "--output-dir",
        default="data/eval",
        metavar="DIR",
        help="Directory to write the comparison report (default: data/eval)",
    )
    p.add_argument(
        "--models",
        nargs="+",
        metavar="MODEL",
        default=None,
        help=(
            "Models to run (default: all 3). "
            "Accepts aliases: gemma, phi3, zeroday, or full Ollama model names."
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- Load inputs ---
    benchmark_path = Path(args.benchmark)
    cache_path = Path(args.retrieval_cache)
    output_dir = Path(args.output_dir)

    if not benchmark_path.exists():
        print(f"[ERROR] Benchmark file not found: {benchmark_path}", file=sys.stderr)
        return 1
    if not cache_path.exists():
        print(f"[ERROR] Retrieval cache not found: {cache_path}", file=sys.stderr)
        return 1

    raw_queries: list[dict] = _load_json(benchmark_path)  # type: ignore[assignment]

    retrieval_cache: dict[str, str] = _load_json(cache_path)  # type: ignore[assignment]

    queries = _merge_context(raw_queries, retrieval_cache)
    if not queries:
        print("[ERROR] No queries with retrieval context -- nothing to run.", file=sys.stderr)
        return 1

    # --- Build adapters ---
    model_names = _resolve_models(args.models)
    adapters = [OllamaAdapter(m) for m in model_names]
    print(f"[INFO] Running {len(queries)} queries against {len(adapters)} models: {model_names}")

    # --- Run comparison ---
    results = run_model_comparison(queries, adapters)

    # --- Write report ---
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build benchmark lookup for category enrichment
    benchmark_lookup = {q["id"]: q for q in raw_queries}

    generate_comparison_report(results, str(output_dir), benchmark=benchmark_lookup)
    print(f"[INFO] Report written to: {output_dir / 'comparison_report.json'}")

    # --- Console summary ---
    _print_summary(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
