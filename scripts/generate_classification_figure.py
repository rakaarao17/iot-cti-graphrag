"""Figure: LLM classification accuracy vs the XGBoost baseline (division of labor)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

d = json.load(open("data/eval/classification_test_report.json", encoding="utf-8"))
order = ["phi3:latest", "zeroday-phi3-ciciot-v2:latest", "gemma4:e2b"]
labels = ["phi3", "zeroday-phi3\n(classifier f.t.)", "gemma4*"]
acc = [d[m]["accuracy"] for m in order]
valid = [d[m]["valid_label_rate"] for m in order]

x = np.arange(len(order)); w = 0.38
fig, ax = plt.subplots(figsize=(8.5, 5.5))
ax.bar(x - w/2, acc, w, label="Classification accuracy", color="#C44E52",
       edgecolor="black", linewidth=0.5)
ax.bar(x + w/2, valid, w, label="Valid-label rate", color="#8172B3",
       edgecolor="black", linewidth=0.5)
for i in range(len(order)):
    ax.text(x[i]-w/2, acc[i]+0.02, f"{acc[i]:.2f}", ha="center", fontsize=9, fontweight="bold")
    ax.text(x[i]+w/2, valid[i]+0.02, f"{valid[i]:.2f}", ha="center", fontsize=9, fontweight="bold")
# XGBoost reference (the correct tool for classification)
ax.axhline(0.656, color="#2E7D32", ls="--", lw=1.6)
ax.text(2.35, 0.67, "XGBoost baseline\n0.656 macro-F1\n(correct tool)", color="#2E7D32",
        fontsize=8, ha="right", fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05)
ax.set_ylabel("Score")
ax.set_title("Attack classification: LLMs are weak; the tabular model wins\n"
             "(30 flows, 34 classes) - use XGBoost to classify, LLMs to explain",
             fontweight="bold")
ax.legend(loc="upper left")
ax.text(0.02, -0.13, "*gemma4 returned empty (partial-CPU/VRAM glitch), not a true 0.",
        transform=ax.transAxes, fontsize=7, color="#666")
fig.tight_layout()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/fig_classification_test.png", dpi=300, bbox_inches="tight")
print("  [OK] results/fig_classification_test.png")
