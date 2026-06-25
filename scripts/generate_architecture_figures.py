"""Generate architecture / pipeline / KG-schema diagrams with matplotlib.

All diagrams are drawn from code (reproducible, not AI-generated images) and use
the project's REAL knowledge-graph counts. Writes 300-DPI PNGs to results/.
Run: python scripts/generate_architecture_figures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path("results"); OUT.mkdir(exist_ok=True)
plt.rcParams.update({"savefig.dpi": 300, "font.size": 10})

# Real KG statistics (from live Neo4j 'iot' database, integration-test readout).
KG_NODES = {"Flow": 8643068, "Port": 65427, "Device": 667770, "AttackType": 34,
            "AttackCategory": 10, "MITRETechnique": 9, "Protocol": 4, "Dataset": 2}
KG_RELS = [("Device", "INITIATES", "Flow", 8643068), ("Flow", "TARGETS", "Device", 8643068),
           ("Flow", "USES", "Port", 8643068), ("Flow", "CLASSIFIED_AS", "AttackType", 8643068),
           ("AttackType", "BELONGS_TO", "AttackCategory", 34), ("AttackType", "MAPS_TO", "MITRETechnique", 22),
           ("Device", "COMMUNICATES_WITH", "Device", 518841)]


def _box(ax, x, y, w, h, text, fc, fs=10, ec="#333333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, wrap=True)


def _arrow(ax, p1, p2, color="#444444", style="-|>"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14,
                                 color=color, lw=1.4, shrinkA=2, shrinkB=2))


def fig_architecture():
    fig, ax = plt.subplots(figsize=(11, 7)); ax.set_xlim(0, 12); ax.set_ylim(0, 9); ax.axis("off")
    ax.set_title("Hexagonal Architecture - IoT CTI GraphRAG", fontsize=14, fontweight="bold")
    _box(ax, 0.4, 7.6, 11.2, 1.0, "CLI  (src/cli/main.py)  -  Interactive Threat Analyst", "#DCE6F2", 11)
    # Ports (interfaces)
    _box(ax, 0.4, 6.0, 3.6, 1.2, "Ports (interfaces)\nLLMPort | GraphPort | EmbeddingPort", "#FBE6C8", 9)
    # Adapters
    _box(ax, 4.2, 6.0, 7.4, 1.2, "Adapters\nOllamaAdapter | Neo4jAdapter | Mock* (testing)", "#D7EBD3", 9)
    # Core
    _box(ax, 0.4, 4.6, 11.2, 1.0, "Core  (src/core)  -  Config (single source, ADR-0007) | Exception hierarchy", "#E8DCEF", 9)
    # Services (6 stages)
    stages = ["1. Data\nAcquisition", "2. Feature\nExtraction", "3. Knowledge\nGraph",
              "4. Graph\nEmbeddings", "5. GraphRAG\nRetrieval", "6. Threat\nExplanation"]
    for i, s in enumerate(stages):
        _box(ax, 0.4 + i*1.92, 2.8, 1.8, 1.3, s, "#CFE2F3", 8)
    ax.text(6, 4.25, "src/services/  (6 pipeline stages)", ha="center", fontsize=9, style="italic")
    # External systems
    _box(ax, 0.4, 0.8, 3.4, 1.2, "Neo4j\n(9.4M nodes, 35M rels)", "#F4CCCC", 9)
    _box(ax, 4.2, 0.8, 3.4, 1.2, "Ollama (local LLM)\nphi3 / gemma4 / zeroday", "#F4CCCC", 9)
    _box(ax, 8.0, 0.8, 3.6, 1.2, "sentence-transformers\nall-MiniLM-L6-v2 (384d)", "#F4CCCC", 9)
    for sx in [2.1, 5.9, 9.8]:
        _arrow(ax, (sx, 2.8), (sx, 2.0))
    _arrow(ax, (6, 7.6), (6, 7.2)); _arrow(ax, (6, 6.0), (6, 5.6)); _arrow(ax, (6, 4.6), (6, 4.1))
    fig.savefig(OUT / "fig_architecture.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_architecture.png")


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(12, 3.2)); ax.set_xlim(0, 12); ax.set_ylim(0, 3); ax.axis("off")
    ax.set_title("End-to-End Pipeline (6 stages)", fontsize=13, fontweight="bold")
    steps = ["IoT-23 +\nCICIoT2023\n(raw flows)", "Feature\nExtraction\n(Pandas)",
             "Neo4j KG\n9.4M nodes", "node2vec +\nMiniLM\nembeddings",
             "Dual retrieval\nCypher + Vector", "LLM threat\nexplanation\n+ grounding"]
    cols = ["#F4CCCC", "#FCE5CD", "#FFF2CC", "#D9EAD3", "#D0E0E3", "#CFE2F3"]
    w = 1.7
    for i, (s, c) in enumerate(zip(steps, cols)):
        x = 0.2 + i*1.95
        _box(ax, x, 1.0, w, 1.3, s, c, 8)
        if i < len(steps) - 1:
            _arrow(ax, (x + w, 1.65), (x + 1.95, 1.65))
    fig.savefig(OUT / "fig_pipeline.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_pipeline.png")


def fig_kg_schema():
    fig, ax = plt.subplots(figsize=(11, 7)); ax.set_xlim(0, 12); ax.set_ylim(0, 9); ax.axis("off")
    ax.set_title("Knowledge Graph Schema (real node/relationship counts)", fontsize=13, fontweight="bold")
    pos = {"Device": (2, 6.5), "Flow": (6, 6.5), "Port": (10, 6.5), "AttackType": (6, 3.5),
           "AttackCategory": (2.2, 1.5), "MITRETechnique": (9.8, 1.5), "Protocol": (10, 3.5), "Dataset": (2, 3.5)}
    colors = {"Device": "#CFE2F3", "Flow": "#F9CB9C", "Port": "#D9D2E9", "AttackType": "#EA9999",
              "AttackCategory": "#FFE599", "MITRETechnique": "#B6D7A8", "Protocol": "#D5A6BD", "Dataset": "#B7B7B7"}
    for n, (x, y) in pos.items():
        cnt = KG_NODES.get(n, 0)
        _box(ax, x-0.95, y-0.45, 1.9, 0.9, f"{n}\n{cnt:,}", colors.get(n, "#EEE"), 8.5)
    # detect pairs that have arrows in both directions, so we can curve them apart
    pairs = {}
    for src, rel, dst, _ in KG_RELS:
        pairs[frozenset((src, dst))] = pairs.get(frozenset((src, dst)), 0) + 1
    seen = {}
    for src, rel, dst, cnt in KG_RELS:
        (x1, y1), (x2, y2) = pos[src], pos[dst]
        if src == dst:
            ax.annotate("", xy=(x1-0.5, y1+0.55), xytext=(x1+0.5, y1+0.55),
                        arrowprops=dict(arrowstyle="-|>", color="#999",
                                        connectionstyle="arc3,rad=-1.6"))
            ax.text(x1, y1+1.15, rel, fontsize=7, color="#555", ha="center")
            continue
        key = frozenset((src, dst))
        bidir = pairs[key] > 1
        idx = seen.get(key, 0); seen[key] = idx + 1
        rad = 0.0 if not bidir else (0.22 if idx == 0 else -0.22)
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                     color="#888", lw=1.3, shrinkA=14, shrinkB=14,
                     connectionstyle=f"arc3,rad={rad}"))
        lx, ly = (x1+x2)/2, (y1+y2)/2
        off = 0.0 if not bidir else (0.45 if idx == 0 else -0.45)
        ax.text(lx, ly + 0.12 + off, rel, fontsize=7, color="#444", ha="center",
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.5))
    fig.savefig(OUT / "fig_kg_schema.png", bbox_inches="tight"); plt.close(fig)
    print("  [OK] fig_kg_schema.png")


if __name__ == "__main__":
    print("Generating architecture/pipeline/schema diagrams...")
    fig_architecture(); fig_pipeline(); fig_kg_schema()
    print("Done -> results/fig_architecture.png, fig_pipeline.png, fig_kg_schema.png")
