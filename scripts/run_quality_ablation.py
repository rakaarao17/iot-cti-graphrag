"""Answer-QUALITY ablation: adds a grounding metric to all 50 x 3 conditions.

The committed ablation (ablation_results.json) measures only retrieval latency and
result count. This script reuses the EXACT retrieved contexts from that file,
generates an answer for each with the strong local model, and measures grounding
(fraction of answer entities supported by the retrieved context). This gives a
genuine answer-quality metric on the full 50-query benchmark, per retrieval
condition -- addressing the "headline metric is a weak proxy" gap.

Non-destructive: writes data/eval/ablation_quality_results.json and quality_report.*.
Run: python scripts/run_quality_ablation.py   (Neo4j not needed; Ollama required)
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.threat_explanation.ollama_client import OllamaClient
from src.services.threat_explanation.grounding import check_grounding

# phi3 is the genuinely robust model: zeroday-phi3 degenerates into gibberish on
# long retrieved contexts (while still scoring grounding ~1.0). We therefore use
# phi3 and report BOTH grounding and a coherence heuristic so the quality metric
# cannot be gamed by token-echoing gibberish.
MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")


def coherence(text: str) -> float:
    """Heuristic 0-1 coherence: penalizes glued-gibberish tokens, rewards real words."""
    words = re.findall(r"[A-Za-z]{2,}", text)
    if not words:
        return 0.0
    real = sum(1 for w in words if re.search(r"[aeiou]", w.lower()) and len(w) <= 18)
    junk = sum(1 for w in words if len(w) > 18)
    return round(max(0.0, real / len(words) - junk / len(words)), 3)
ABL = Path("data/eval/ablation_results.json")
QUERIES = Path("data/eval/curated_queries.json")
OUT = Path("data/eval/ablation_quality_results.json")
COND = ["cypher_only", "vector_only", "combined"]

PROMPT = """You are an IoT cybersecurity analyst. Using ONLY the retrieved context below,
answer the question concisely and factually. Cite specific entities (IPs, attack
names, MITRE IDs, counts) from the context. If the context does not contain the
answer, say so explicitly.

Retrieved context:
{context}

Question: {query}

Answer:"""


def main():
    records = json.load(open(ABL, encoding="utf-8"))
    rtype = {}
    if QUERIES.exists():
        for q in json.load(open(QUERIES, encoding="utf-8")):
            rtype[q.get("id")] = q.get("retrieval_type", q.get("type", "unknown"))

    client = OllamaClient(model=MODEL)
    print(f"Quality ablation: {len(records)} (query x condition) with model={MODEL}")
    out = []
    t_all = time.time()
    for i, r in enumerate(records, 1):
        ctx = r.get("context_text", "")
        prompt = PROMPT.format(context=ctx[:6000], query=r["query"])
        t0 = time.time()
        answer = client.generate(prompt)
        gen_ms = (time.time() - t0) * 1000
        g = check_grounding(answer, ctx)
        out.append({
            "query_id": r["query_id"],
            "retrieval_type": rtype.get(r["query_id"], "unknown"),
            "condition": r["condition"],
            "grounding_ratio": round(g.grounding_ratio, 4),
            "coherence": coherence(answer),
            "answer_tokens": len(answer.split()),
            "gen_latency_ms": round(gen_ms, 1),
            "n_ungrounded": len(g.ungrounded_entities),
        })
        if i % 15 == 0 or i == len(records):
            print(f"  {i}/{len(records)} done ({time.time()-t_all:.0f}s elapsed)")
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- stats: grounding AND coherence by condition ----
    import numpy as np
    from scipy.stats import kruskal

    def stat_block(metric):
        by = {c: [o[metric] for o in out if o["condition"] == c] for c in COND}
        H, p = kruskal(*[by[c] for c in COND])
        rows, summ = [], {}
        for c in COND:
            a = np.array(by[c])
            rows.append(f"| {c} | {a.mean():.3f} | {np.median(a):.3f} | {a.std():.3f} | {a.min():.3f} | {a.max():.3f} |")
            summ[c] = {"mean": float(a.mean()), "median": float(np.median(a)), "std": float(a.std()), "n": int(a.size)}
        return rows, summ, float(H), float(p)

    g_rows, g_sum, gH, gp = stat_block("grounding_ratio")
    c_rows, c_sum, cH, cp = stat_block("coherence")
    sig = lambda p: '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'ns'))

    lines = [
        "# Answer-Quality Ablation (grounding + coherence, full 50-query benchmark)",
        "",
        f"**Model:** {MODEL}  |  **Queries:** 50  |  **Conditions:** 3  |  **Observations:** {len(out)}",
        "",
        "Two metrics are reported because grounding alone is gameable: a model can echo",
        "context tokens as gibberish and still score ~1.0 grounding. Coherence (0-1 heuristic)",
        "penalizes glued-gibberish tokens. A good answer needs BOTH high grounding and high coherence.",
        "",
        "## Grounding ratio by condition",
        "",
        "| Condition | Mean | Median | Std | Min | Max |",
        "|-----------|------|--------|-----|-----|-----|",
        *g_rows,
        "",
        f"Kruskal-Wallis: **H={gH:.3f}, p={gp:.6f} {sig(gp)}**",
        "",
        "## Coherence by condition",
        "",
        "| Condition | Mean | Median | Std | Min | Max |",
        "|-----------|------|--------|-----|-----|-----|",
        *c_rows,
        "",
        f"Kruskal-Wallis: **H={cH:.3f}, p={cp:.6f} {sig(cp)}**",
        "",
        "_Generated by scripts/run_quality_ablation.py_",
    ]
    Path("data/eval/quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("data/eval/quality_report.json").write_text(json.dumps(
        {"model": MODEL,
         "grounding": {"by_condition": g_sum, "kruskal_H": gH, "kruskal_p": gp},
         "coherence": {"by_condition": c_sum, "kruskal_H": cH, "kruskal_p": cp}}, indent=2), encoding="utf-8")

    print("\n--- QUALITY BY CONDITION (grounding / coherence) ---")
    for c in COND:
        print(f"  {c:12s} grounding={g_sum[c]['mean']:.3f}  coherence={c_sum[c]['mean']:.3f}  n={g_sum[c]['n']}")
    print(f"  KW grounding: H={gH:.3f} p={gp:.6f} | KW coherence: H={cH:.3f} p={cp:.6f}")
    print(f"\nSaved: {OUT}, data/eval/quality_report.{{md,json}}  ({time.time()-t_all:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
