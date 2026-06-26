"""Figure: the input-format effect on the fine-tuned classifier (fair comparison)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

zeek = json.load(open("data/eval/classification_test_report.json", encoding="utf-8"))
nat = json.load(open("data/eval/zeroday_native_report.json", encoding="utf-8"))

bars = [
    ("zeroday\n(Zeek-flow,\nwrong format)", zeek["zeroday-phi3-ciciot-v2:latest"]["accuracy"], "#C44E52"),
    ("zeroday\n(native 39-feat)", nat["zeroday-phi3-ciciot-v2:latest"]["accuracy"], "#55A868"),
    ("phi3\n(native 39-feat)", nat["phi3:latest"]["accuracy"], "#4C72B0"),
]
labels = [b[0] for b in bars]; vals = [b[1] for b in bars]; cols = [b[2] for b in bars]

fig, ax = plt.subplots(figsize=(8.5, 5.5))
b = ax.bar(range(len(bars)), vals, color=cols, edgecolor="black", linewidth=0.6, width=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontweight="bold")
ax.axhline(0.656, color="#2E7D32", ls="--", lw=1.6)
ax.text(2.4, 0.67, "XGBoost 0.656\n(best classifier)", color="#2E7D32", fontsize=8,
        ha="right", fontweight="bold")
ax.annotate("native format:\n4.7x accuracy", xy=(1, vals[1]), xytext=(0.5, 0.58),
            fontsize=8, color="#2E7D32", ha="center",
            arrowprops=dict(arrowstyle="->", color="#2E7D32"))
ax.set_xticks(range(len(bars))); ax.set_xticklabels(labels)
ax.set_ylim(0, 0.8); ax.set_ylabel("Classification accuracy")
ax.set_title("Fine-tuned classifier needs its native input format\n"
             "zeroday: 0.10 (wrong format) -> 0.47 (native), and beats phi3 0.40",
             fontweight="bold")
fig.tight_layout()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/fig_zeroday_native.png", dpi=300, bbox_inches="tight")
print("  [OK] results/fig_zeroday_native.png")
