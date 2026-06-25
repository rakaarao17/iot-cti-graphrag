"""Additional dissertation result figures from committed eval data (no services).

- fig_latency_heatmap : median retrieval latency, retrieval-type x condition
- fig_baseline_perclass : per-class F1 of the full XGBoost baseline (34 classes)
- fig_feature_importance : top-15 XGBoost feature importances
Run: python scripts/generate_result_figures_extra.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EVAL = Path("data/eval"); OUT = Path("results"); OUT.mkdir(exist_ok=True)
plt.rcParams.update({"savefig.dpi": 300, "font.size": 10})
COND = ["cypher_only", "vector_only", "combined"]
CLBL = ["Cypher", "Vector", "Combined"]


def fig_latency_heatmap():
    brt = json.load(open(EVAL / "statistical_report.json", encoding="utf-8"))["by_retrieval_type"]
    types = sorted(brt.keys())
    M = np.array([[np.median(brt[t][c]) / 1000.0 for c in COND] for t in types])
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(M, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(CLBL)
    ax.set_yticks(range(len(types))); ax.set_yticklabels([t.replace("_", " ") for t in types])
    for i in range(len(types)):
        for j in range(3):
            ax.text(j, i, f"{M[i,j]:.1f}", ha="center", va="center",
                    color="black" if M[i, j] < M.max()*0.6 else "white", fontsize=8)
    ax.set_title("Median retrieval latency (s) by query type x condition", fontweight="bold")
    fig.colorbar(im, ax=ax, label="seconds"); fig.tight_layout()
    fig.savefig(OUT / "fig_latency_heatmap.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_latency_heatmap.png")


def fig_baseline_perclass():
    d = json.load(open(EVAL / "baseline_full_report.json", encoding="utf-8"))["per_class_f1"]
    items = sorted(d.items(), key=lambda x: x[1])
    names = [k for k, _ in items]; vals = [v for _, v in items]
    colors = ["#C44E52" if v < 0.3 else ("#DD8452" if v < 0.6 else "#55A868") for v in vals]
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.barh(range(len(names)), vals, color=colors, edgecolor="black", linewidth=0.4)
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("Per-class F1"); ax.set_xlim(0, 1)
    ax.axvline(np.mean(vals), color="navy", ls="--", lw=1, label=f"macro-F1 = {np.mean(vals):.3f}")
    ax.set_title("Full XGBoost baseline: per-class F1 (34 classes)", fontweight="bold")
    ax.legend(loc="lower right"); fig.tight_layout()
    fig.savefig(OUT / "fig_baseline_perclass.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_baseline_perclass.png")


def fig_feature_importance():
    d = json.load(open(EVAL / "baseline_full_report.json", encoding="utf-8"))["feature_importances"]
    top = sorted(d.items(), key=lambda x: x[1], reverse=True)[:15][::-1]
    names = [k for k, _ in top]; vals = [v for _, v in top]
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.barh(range(len(names)), vals, color="#4C72B0", edgecolor="black", linewidth=0.4)
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names)
    ax.set_xlabel("Importance (gain)")
    ax.set_title("Full XGBoost baseline: top-15 feature importances", fontweight="bold")
    for i, v in enumerate(vals):
        ax.text(v + 0.003, i, f"{v:.3f}", va="center", fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig_feature_importance.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_feature_importance.png")


if __name__ == "__main__":
    print("Generating extra result figures...")
    fig_latency_heatmap(); fig_baseline_perclass(); fig_feature_importance()
    print("Done.")
