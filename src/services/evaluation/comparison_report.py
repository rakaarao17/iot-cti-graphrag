"""
Comparison report generator.

Aggregates ModelComparisonResult list into a structured JSON + Markdown report.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from src.services.evaluation.llm_comparison import ModelComparisonResult


def generate_comparison_report(
    results: list[ModelComparisonResult],
    output_dir: str = "data/eval",
    benchmark: dict[str, dict] | None = None,
) -> dict:
    """
    Aggregate ModelComparisonResult list into a comparison report.

    Computes per-model:
      - mean_latency_ms
      - median_latency_ms
      - mean_grounding_ratio
      - mean_output_tokens
      - error_rate (fraction of responses with error != None)

    Optional `benchmark` parameter: dict mapping query_id -> query dict
    (with a "category" key). Used to populate per_query[].category.
    If not provided, category defaults to "unknown".

    Saves:
      - {output_dir}/comparison_report.json
      - {output_dir}/comparison_report.md

    Returns the report dict.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Collect per-model stats
    # -----------------------------------------------------------------------
    # model_name -> list of (latency_ms, grounding_ratio, output_tokens, has_error)
    model_data: dict[str, dict] = {}

    for result in results:
        for model_name, response in result.responses.items():
            if model_name not in model_data:
                model_data[model_name] = {
                    "deployment": response.deployment,
                    "latencies": [],
                    "grounding_ratios": [],
                    "output_tokens": [],
                    "errors": [],
                }
            d = model_data[model_name]
            d["latencies"].append(response.latency_ms)
            d["output_tokens"].append(response.output_tokens)
            d["errors"].append(1 if response.error is not None else 0)

            # Grounding ratio from grounding dict
            gr = result.grounding.get(model_name)
            d["grounding_ratios"].append(gr.grounding_ratio if gr is not None else 0.0)

    # Aggregate
    models_section: dict[str, dict] = {}
    for model_name, d in model_data.items():
        latencies = d["latencies"]
        grounding_ratios = d["grounding_ratios"]
        output_tokens = d["output_tokens"]
        errors = d["errors"]
        n = len(latencies)

        models_section[model_name] = {
            "deployment": d["deployment"],
            "mean_latency_ms": round(statistics.mean(latencies), 3) if n else 0.0,
            "median_latency_ms": round(statistics.median(latencies), 3) if n else 0.0,
            "mean_grounding_ratio": round(statistics.mean(grounding_ratios), 3) if n else 0.0,
            "mean_output_tokens": int(round(statistics.mean(output_tokens))) if n else 0,
            "error_rate": round(sum(errors) / n, 3) if n else 0.0,
        }

    # -----------------------------------------------------------------------
    # Build per_query section
    # -----------------------------------------------------------------------
    per_query = []
    for result in results:
        category = "unknown"
        if benchmark is not None and result.query_id in benchmark:
            category = benchmark[result.query_id].get("category", "unknown")

        query_entry: dict = {
            "query_id": result.query_id,
            "category": category,
            "responses": {},
        }
        for model_name, response in result.responses.items():
            gr = result.grounding.get(model_name)
            query_entry["responses"][model_name] = {
                "latency_ms": response.latency_ms,
                "grounding_ratio": gr.grounding_ratio if gr is not None else 0.0,
                "output_tokens": response.output_tokens,
                "response_text": response.response_text,
            }
        per_query.append(query_entry)

    # -----------------------------------------------------------------------
    # Assemble report dict
    # -----------------------------------------------------------------------
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(results),
        "token_count_note": "input_tokens and output_tokens are estimates (character_count // 4)",
        "models": models_section,
        "per_query": per_query,
    }

    # -----------------------------------------------------------------------
    # Write JSON
    # -----------------------------------------------------------------------
    json_path = out / "comparison_report.json"
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    # -----------------------------------------------------------------------
    # Write Markdown
    # -----------------------------------------------------------------------
    md_path = out / "comparison_report.md"
    _write_markdown(report, md_path)

    return report


# ---------------------------------------------------------------------------
# Markdown writer
# ---------------------------------------------------------------------------

def _write_markdown(report: dict, path: Path) -> None:
    """Write a human-readable Markdown report."""
    lines = [
        "# LLM Model Comparison Report",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Total queries:** {report['query_count']}",
        "",
        "## Per-Model Summary",
        "",
        "| Model | Deployment | Mean Latency (ms) | Median Latency (ms) | Mean Grounding | Mean Tokens | Error Rate |",
        "|-------|------------|-------------------|---------------------|----------------|-------------|------------|",
    ]

    for model_name, stats in report["models"].items():
        lines.append(
            f"| {model_name} "
            f"| {stats['deployment']} "
            f"| {stats['mean_latency_ms']:.1f} "
            f"| {stats['median_latency_ms']:.1f} "
            f"| {stats['mean_grounding_ratio']:.3f} "
            f"| {stats['mean_output_tokens']:.0f} "
            f"| {stats['error_rate']:.3f} |"
        )

    lines += ["", "## Per-Query Grounding Ratios", ""]

    if report["per_query"]:
        # Build header from union of model names across all per_query entries
        model_names = sorted({
            m for pq in report.get("per_query", [])
            for m in pq.get("responses", {}).keys()
        })
        header = "| Query ID | Category | " + " | ".join(model_names) + " |"
        divider = "|----------|----------|" + "|".join(["----------"] * len(model_names)) + "|"
        lines += [header, divider]

        for entry in report["per_query"]:
            ratios = []
            for m in model_names:
                r = entry["responses"].get(m, {})
                ratios.append(f"{r.get('grounding_ratio', 0.0):.3f}")
            lines.append(
                f"| {entry['query_id']} | {entry['category']} | "
                + " | ".join(ratios)
                + " |"
            )
    else:
        lines.append("_No queries run._")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
