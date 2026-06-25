"""Figure: answer quality (grounding faithfulness + coherence) by retrieval condition."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

d = json.load(open("data/eval/quality_report.json", encoding="utf-8"))
COND = ["cypher_only", "vector_only", "combined"]
LBL = ["Cypher", "Vector", "Combined"]
g = [d["grounding"]["by_condition"][c]["mean"] for c in COND]
gsd = [d["grounding"]["by_condition"][c]["std"] for c in COND]
c = [d["coherence"]["by_condition"][c2]["mean"] for c2 in COND]
csd = [d["coherence"]["by_condition"][c2]["std"] for c2 in COND]

x = np.arange(len(COND)); w = 0.38
fig, ax = plt.subplots(figsize=(8, 5.2))
b1 = ax.bar(x - w/2, g, w, yerr=gsd, capsize=5, label="Grounding (faithfulness)",
            color="#4C72B0", edgecolor="black", linewidth=0.5)
b2 = ax.bar(x + w/2, c, w, yerr=csd, capsize=5, label="Coherence",
            color="#55A868", edgecolor="black", linewidth=0.5)
for b, v in list(zip(b1, g)) + list(zip(b2, c)):
    ax.text(b.get_x()+b.get_width()/2, v+0.015, f"{v:.2f}", ha="center", fontsize=9, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(LBL); ax.set_ylim(0, 1.15)
ax.set_ylabel("Score (0-1)")
gp = d["grounding"]["kruskal_p"]; cp = d["coherence"]["kruskal_p"]
ax.set_title(f"Answer quality by retrieval condition (phi3, n=50 each)\n"
             f"grounding differs (KW p={gp:.3f}); coherence flat (KW p={cp:.2f})",
             fontweight="bold")
ax.legend(loc="lower right"); ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
Path("results").mkdir(exist_ok=True)
fig.savefig("results/fig_quality_ablation.png", dpi=300, bbox_inches="tight")
print("  [OK] results/fig_quality_ablation.png")
