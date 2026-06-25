"""Generate publication-quality figures for the evaluation RESULTS.

Reads only committed result JSONs in data/eval/ (no Neo4j/Ollama needed) and
writes 300-DPI figures to results/. Covers the three experiments + the baselines,
which previously had no visualizations (only descriptive dataset plots existed).

Run: python scripts/generate_result_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EVAL = Path("data/eval")
OUT = Path("results")
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 300, "savefig.dpi": 300, "font.size": 11,
                     "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True})
COND = ["cypher_only", "vector_only", "combined"]
COND_LBL = ["Cypher-only", "Vector-only", "Combined"]
COLORS = ["#4C72B0", "#DD8452", "#55A868"]


def _load(name):
    return json.load(open(EVAL / name, encoding="utf-8"))


def fig_ablation():
    rows = _load("ablation_results.json")
    lat = {c: [] for c in COND}
    cnt = {c: [] for c in COND}
    for r in rows:
        c = r["condition"]
        if c in lat:
            lat[c].append(r["latency_ms"] / 1000.0)
            cnt[c].append(len(r.get("results", [])))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    for i, (data, title, ylab) in enumerate([
            (lat, "Retrieval latency by condition", "Latency (s)"),
            (cnt, "Context size by condition", "Results returned")]):
        bp = ax[i].boxplot([data[c] for c in COND], labels=COND_LBL,
                           patch_artist=True, showmeans=True, widths=0.6)
        for patch, col in zip(bp["boxes"], COLORS):
            patch.set_facecolor(col); patch.set_alpha(0.7)
        ax[i].set_title(title); ax[i].set_ylabel(ylab)
    fig.suptitle("GraphRAG Ablation (n=50 queries x 3 conditions)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "fig_ablation_boxplots.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_ablation_boxplots.png")


def fig_judge():
    s = _load("llm_judge_summary.json")
    means, sds = [], []
    for c in COND:
        d = s.get(c, {})
        scores = d.get("scores")
        if scores:
            means.append(float(np.mean(scores))); sds.append(float(np.std(scores)))
        else:
            means.append(float(d.get("mean", 0))); sds.append(float(d.get("std", 0)))
    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(COND_LBL, means, yerr=sds, capsize=6, color=COLORS, alpha=0.85,
                  edgecolor="black", linewidth=0.6)
    for b, m in zip(bars, means):
        ax.text(b.get_x() + b.get_width()/2, m + 0.05, f"{m:.2f}", ha="center", fontweight="bold")
    ax.set_ylim(0, 5); ax.set_ylabel("LLM-judge relevance (1-5)")
    ax.set_title("Retrieval relevance (LLM-as-judge, n=20)\nFriedman p=0.00044", fontweight="bold")
    fig.tight_layout(); fig.savefig(OUT / "fig_llm_judge_relevance.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_llm_judge_relevance.png")


def fig_models():
    d = _load("comparison_report.json")
    models = d["models"]  # dict: name -> stats
    names = list(models.keys())
    short = [n.split(":")[0].replace("zeroday-phi3-ciciot-v2", "zeroday-phi3") for n in names]
    grounding = [models[n].get("mean_grounding_ratio", 0) for n in names]
    err = [models[n].get("error_rate", 0) for n in names]
    x = np.arange(len(short)); w = 0.38
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar(x - w/2, grounding, w, label="Mean grounding", color="#55A868", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, err, w, label="Error rate", color="#C44E52", edgecolor="black", linewidth=0.5)
    for i, g in enumerate(grounding):
        ax.text(i - w/2, g + 0.02, f"{g:.2f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(short, rotation=10)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Ratio"); ax.legend()
    ax.set_title("Local LLM comparison: grounding vs error rate (n=20)", fontweight="bold")
    fig.tight_layout(); fig.savefig(OUT / "fig_model_comparison.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_model_comparison.png")


def fig_baselines():
    items = [("Sample\n(25k, 10 feat)", "baseline_sample_report.json"),
             ("Unified\n(1.5M, 10 feat)", "baseline_unified_report.json"),
             ("Full CICIoT\n(4.3M, 46 feat)", "baseline_full_report.json")]
    labels, f1s, aucs = [], [], []
    for lab, fn in items:
        p = EVAL / fn
        if p.exists():
            d = json.load(open(p, encoding="utf-8"))
            labels.append(lab); f1s.append(d.get("macro_f1", 0)); aucs.append(d.get("auc_roc", 0))
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.bar(x - w/2, f1s, w, label="Macro-F1", color="#4C72B0", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, aucs, w, label="AUC-ROC", color="#8172B3", edgecolor="black", linewidth=0.5)
    for i in range(len(labels)):
        ax.text(i - w/2, f1s[i] + 0.02, f"{f1s[i]:.3f}", ha="center", fontsize=9, fontweight="bold")
        ax.text(i + w/2, aucs[i] + 0.02, f"{aucs[i]:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score"); ax.legend()
    ax.set_title("XGBoost tabular baselines (34 classes)", fontweight="bold")
    fig.tight_layout(); fig.savefig(OUT / "fig_baselines.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_baselines.png")


if __name__ == "__main__":
    print("Generating result figures from committed data/eval JSONs...")
    fig_ablation(); fig_judge(); fig_models(); fig_baselines()
    print("Done -> results/fig_*.png")
