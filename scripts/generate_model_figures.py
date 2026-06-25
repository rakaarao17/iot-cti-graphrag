"""Model-comparison figures from data/eval/model_readout.json (no services).

- fig_grounding_vs_tokens : scatter showing high grounding at ~0 tokens (the metric flaw)
- fig_model_readout       : grounding vs coherence by model x mode
Run: python scripts/generate_model_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

EVAL = Path("data/eval"); OUT = Path("results"); OUT.mkdir(exist_ok=True)
plt.rcParams.update({"savefig.dpi": 300, "font.size": 10})
SHORT = {"phi3:latest": "phi3", "zeroday-phi3-ciciot-v2:latest": "zeroday-phi3", "gemma4:e2b": "gemma4"}
COLOR = {"phi3": "#55A868", "zeroday-phi3": "#C44E52", "gemma4": "#4C72B0"}


def fig_grounding_vs_tokens():
    data = json.load(open(EVAL / "model_readout.json", encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for m in COLOR:
        pts = [(d["tokens"], d["grounding"]) for d in data if SHORT.get(d["model"]) == m]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, s=55, alpha=0.75, color=COLOR[m], edgecolor="black",
                       linewidth=0.4, label=m)
    ax.axvspan(0, 15, color="red", alpha=0.08)
    ax.text(7.5, 0.05, "near-empty\nanswers", ha="center", fontsize=8, color="#a00")
    ax.set_xlabel("Answer length (tokens)"); ax.set_ylabel("Grounding ratio")
    ax.set_title("Why grounding is gameable: empty answers score ~1.0", fontweight="bold")
    ax.grid(alpha=0.3); ax.legend(title="model")
    fig.tight_layout(); fig.savefig(OUT / "fig_grounding_vs_tokens.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_grounding_vs_tokens.png")


def fig_model_readout():
    data = json.load(open(EVAL / "model_readout.json", encoding="utf-8"))
    models = ["phi3", "zeroday-phi3", "gemma4"]; modes = ["generate", "chat"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, metric, title in [(axes[0], "grounding", "Grounding ratio"),
                              (axes[1], "coherence", "Coherence")]:
        x = np.arange(len(models)); w = 0.38
        for k, mode in enumerate(modes):
            vals = [np.mean([d[metric] for d in data if SHORT.get(d["model"]) == m and d["mode"] == mode] or [0])
                    for m in models]
            ax.bar(x + (k-0.5)*w, vals, w, label=mode, edgecolor="black", linewidth=0.5,
                   color=("#8DA0CB" if mode == "generate" else "#FC8D62"))
            for i, v in enumerate(vals):
                ax.text(x[i] + (k-0.5)*w, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)
        ax.set_xticks(x); ax.set_xticklabels(models); ax.set_ylim(0, 1.1)
        ax.set_title(title, fontweight="bold"); ax.legend(title="prompt mode"); ax.grid(alpha=0.3, axis="y")
    fig.suptitle("3-model comparison: grounding looks similar, coherence separates them",
                 fontweight="bold")
    fig.tight_layout(); fig.savefig(OUT / "fig_model_readout.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_model_readout.png")


if __name__ == "__main__":
    print("Generating model figures...")
    fig_grounding_vs_tokens(); fig_model_readout()
    print("Done.")
