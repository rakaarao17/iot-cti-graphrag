"""Figure: corrected usable-rate vs the original gameable grounding metric."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

d = json.load(open("data/eval/corrected_comparison_report.json", encoding="utf-8"))
order = ["phi3:latest", "gemma4:e2b", "zeroday-phi3-ciciot-v2:latest"]
labels = ["phi3", "gemma4", "zeroday-phi3\n(classifier)"]
usable = [d[m]["usable_rate"] for m in order]
raw = [d[m]["mean_grounding_all"] for m in order]

x = np.arange(len(order)); w = 0.38
fig, ax = plt.subplots(figsize=(8.5, 5.5))
b1 = ax.bar(x - w/2, raw, w, label="Original grounding (gameable)", color="#C44E52",
            edgecolor="black", linewidth=0.5, alpha=0.85)
b2 = ax.bar(x + w/2, usable, w, label="Corrected usable-answer rate", color="#55A868",
            edgecolor="black", linewidth=0.5)
for b, v in list(zip(b1, raw)) + list(zip(b2, usable)):
    ax.text(b.get_x()+b.get_width()/2, v+0.02, f"{v:.2f}", ha="center", fontweight="bold", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylim(0, 1.15); ax.set_ylabel("Score")
ax.set_title("LLM comparison: the original metric was gameable\n"
             "(chat mode, n=20) - corrected ranking reverses the original", fontweight="bold")
ax.legend(loc="lower left")
ax.annotate("old metric: 'best'\ncorrected: worst", xy=(2-w/2, raw[2]), xytext=(1.3, 0.72),
            fontsize=8, color="#a00", ha="center",
            arrowprops=dict(arrowstyle="->", color="#a00"))
fig.tight_layout()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/fig_corrected_comparison.png", dpi=300, bbox_inches="tight")
print("  [OK] results/fig_corrected_comparison.png")
