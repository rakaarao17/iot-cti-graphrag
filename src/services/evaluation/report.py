"""Aggregates all evaluation results into a single report."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def generate_evaluation_report(
    baseline_result,
    classification_result,
    ablation_results: list,
    grounding_results: list,
    output_dir: str = "data/eval",
) -> Dict[str, Any]:
    """
    Aggregate all evaluation metrics into a structured report.

    Saves JSON (for reproducibility) and Markdown (for thesis).
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "baseline_xgboost": None if baseline_result is None else {
            "macro_f1": baseline_result.macro_f1,
            "auc_roc": baseline_result.auc_roc,
            "per_class_f1": baseline_result.per_class_f1,
            "n_train": baseline_result.n_train,
            "n_test": baseline_result.n_test,
            "feature_importances": baseline_result.feature_importances,
        },
        "graph_pipeline": None if classification_result is None else {
            "macro_f1": classification_result.macro_f1,
            "weighted_f1": classification_result.weighted_f1,
            "per_class": classification_result.per_class,
        },
        "ablation": {
            "conditions": ["cypher_only", "vector_only", "combined"],
            "results": ablation_results,
            "avg_latency_by_condition": _avg_latency(ablation_results),
        },
        "grounding": {
            "mean_grounding_ratio": _mean_grounding(grounding_results),
            "samples": grounding_results[:5],
        },
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "evaluation_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    md_path = out_dir / "evaluation_report.md"
    md_path.write_text(_render_markdown(report))

    return report


def _avg_latency(ablation_results: list) -> Dict[str, float]:
    from collections import defaultdict
    totals = defaultdict(list)
    for r in ablation_results:
        totals[r["condition"]].append(r.get("latency_ms", 0))
    return {k: round(sum(v) / len(v), 2) for k, v in totals.items()}


def _mean_grounding(grounding_results: list) -> float:
    if not grounding_results:
        return 0.0
    return round(sum(r.get("grounding_ratio", 0) for r in grounding_results) / len(grounding_results), 3)


def _render_markdown(report: Dict) -> str:
    bl = report["baseline_xgboost"]
    gp = report["graph_pipeline"]
    ab = report["ablation"]["avg_latency_by_condition"]
    gr = report["grounding"]["mean_grounding_ratio"]

    lines = [
        f"# Evaluation Report -- {report['generated_at'][:10]}",
        "",
        "## XGBoost Baseline (Tabular Features)",
    ]
    if bl is None:
        lines.append("_Not evaluated -- raw dataset not available._")
    else:
        lines += [
            f"- **Macro F1:** {bl['macro_f1']}",
            f"- **AUC-ROC:** {bl['auc_roc']}",
            f"- **Train / Test:** {bl['n_train']} / {bl['n_test']} flows",
        ]
    lines += [
        "",
        "## Ablation Study -- Retrieval Latency (ms)",
    ]
    for cond, lat in ab.items():
        lines.append(f"- {cond}: {lat} ms")

    lines += [
        "",
        "## LLM Explanation Grounding",
        f"- **Mean Grounding Ratio:** {gr} (fraction of entity mentions present in retrieved context)",
    ]

    if gp is not None:
        lines += [
            "",
            "## Graph Pipeline Classification",
            f"- **Macro F1:** {gp['macro_f1']}",
            f"- **Weighted F1:** {gp['weighted_f1']}",
            "",
            "## Per-Class F1 Scores",
            "| Attack Type | Baseline F1 | Graph Pipeline F1 |",
            "|---|---|---|",
        ]
        for cls in gp["per_class"]:
            baseline_f1 = bl["per_class_f1"].get(cls, "--") if bl else "--"
            graph_f1 = gp["per_class"][cls]["f1"]
            lines.append(f"| {cls} | {baseline_f1} | {graph_f1} |")
    else:
        lines += [
            "",
            "## Graph Pipeline Classification",
            "_Not yet evaluated -- LLM predictions pending._",
        ]

    return "\n".join(lines)
