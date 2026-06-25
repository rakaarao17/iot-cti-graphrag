"""CORRECTED local-LLM comparison for threat explanation.

Fixes three flaws in the original comparison_report:
  1. Prompt format: uses /api/chat (each model's own chat template), not a raw prompt.
  2. Metric gaming: an answer counts only if it is USABLE (>= MIN_WORDS words AND
     coherence >= MIN_COH). Empty/near-empty answers score 0 grounding, not 1, so a
     model cannot "win" by saying nothing.
  3. Honest reporting: the headline metric is usable_rate (did the model actually
     produce a substantive grounded answer), reported alongside grounding/coherence.

Reuses the real retrieved contexts already in ablation_results.json (combined
condition), so Neo4j is not needed; only Ollama. Writes corrected_comparison_report.*
Run: python scripts/run_model_comparison_fixed.py
"""
import json
import re
import sys
import time
from pathlib import Path

import requests
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.services.threat_explanation.grounding import check_grounding

MODELS = ["phi3:latest", "zeroday-phi3-ciciot-v2:latest", "gemma4:e2b"]
N_QUERIES = 20
MIN_WORDS = 20      # an answer shorter than this is not a real explanation
MIN_COH = 0.6       # below this it is gibberish
CHAT_URL = "http://localhost:11434/api/chat"
OPTS = {"temperature": 0.3, "num_predict": 4096}
ABL = Path("data/eval/ablation_results.json")

PROMPT = ("You are an IoT cybersecurity analyst. Using ONLY the retrieved context below, "
          "write a clear factual explanation that answers the question. Cite specific "
          "entities (IPs, attack names, MITRE IDs, counts) from the context.\n\n"
          "Retrieved context:\n{context}\n\nQuestion: {query}\n\nAnswer:")


def coherence(text):
    words = re.findall(r"[A-Za-z]{2,}", text)
    if not words:
        return 0.0
    real = sum(1 for w in words if re.search(r"[aeiou]", w.lower()) and len(w) <= 18)
    junk = sum(1 for w in words if len(w) > 18)
    return round(max(0.0, real / len(words) - junk / len(words)), 3)


def chat(model, prompt):
    r = requests.post(CHAT_URL, json={"model": model, "stream": False, "options": OPTS,
                                      "messages": [{"role": "user", "content": prompt}]}, timeout=600)
    return r.json().get("message", {}).get("content", "")


def main():
    recs = [r for r in json.load(open(ABL, encoding="utf-8")) if r["condition"] == "combined"]
    step = max(1, len(recs) // N_QUERIES)
    picks = recs[::step][:N_QUERIES]
    print(f"Corrected comparison: {len(picks)} queries x {len(MODELS)} models (chat mode)")

    rows = []
    t0 = time.time()
    for qi, rec in enumerate(picks, 1):
        ctx = rec.get("context_text", "")
        prompt = PROMPT.format(context=ctx[:6000], query=rec["query"])
        for model in MODELS:
            try:
                ans = chat(model, prompt)
            except Exception as e:
                ans = ""
                print(f"   {model} ERROR: {e}")
            words = len(ans.split())
            coh = coherence(ans)
            grounding = check_grounding(ans, ctx).grounding_ratio if ans else 0.0
            usable = bool(words >= MIN_WORDS and coh >= MIN_COH)
            rows.append({"q": qi, "model": model, "usable": usable,
                         "grounding": round(grounding, 3), "coherence": coh, "words": words,
                         "eff_grounding": round(grounding, 3) if usable else 0.0})
        print(f"  [{qi}/{len(picks)}] done ({time.time()-t0:.0f}s)")
    Path("data/eval/corrected_comparison_raw.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    # per-model aggregate
    summary = {}
    for m in MODELS:
        sub = [r for r in rows if r["model"] == m]
        summary[m] = {
            "usable_rate": round(np.mean([r["usable"] for r in sub]), 3),
            "mean_eff_grounding": round(np.mean([r["eff_grounding"] for r in sub]), 3),
            "mean_grounding_all": round(np.mean([r["grounding"] for r in sub]), 3),
            "mean_coherence": round(np.mean([r["coherence"] for r in sub]), 3),
            "mean_words": round(np.mean([r["words"] for r in sub]), 1),
            "n": len(sub),
        }

    md = [
        "# Corrected Local-LLM Comparison (threat explanation)",
        "",
        f"**Mode:** /api/chat (each model's own template)  |  **Queries:** {len(picks)}  |  **Models:** {len(MODELS)}",
        f"**Usable answer:** >= {MIN_WORDS} words AND coherence >= {MIN_COH} (else grounding counts as 0).",
        "",
        "This supersedes the original comparison_report, whose grounding metric rewarded",
        "near-empty answers (a 1-word reply scored 1.0). Here a model is credited only for",
        "answers that are actually substantive and coherent.",
        "",
        "| Model | Usable rate | Eff. grounding | Coherence | Mean words | Raw grounding |",
        "|-------|------------|----------------|-----------|------------|---------------|",
    ]
    for m in MODELS:
        s = summary[m]
        md.append(f"| {m} | {s['usable_rate']:.2f} | {s['mean_eff_grounding']:.2f} | "
                  f"{s['mean_coherence']:.2f} | {s['mean_words']:.0f} | {s['mean_grounding_all']:.2f} |")
    md += [
        "",
        "**Read this table as:** *usable rate* = how often the model produced a real answer;",
        "*raw grounding* = the old (gameable) metric. A model with high raw grounding but low",
        "usable rate is winning by saying nothing -- the exact artifact in the original report.",
        "",
        "_Generated by scripts/run_model_comparison_fixed.py_",
    ]
    Path("data/eval/corrected_comparison_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    Path("data/eval/corrected_comparison_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== CORRECTED SUMMARY ===")
    print(f"{'model':34s}{'usable':9s}{'eff_grnd':10s}{'coher':8s}{'words':7s}{'raw_grnd'}")
    for m in MODELS:
        s = summary[m]
        print(f"{m:34s}{s['usable_rate']:<9.2f}{s['mean_eff_grounding']:<10.2f}"
              f"{s['mean_coherence']:<8.2f}{s['mean_words']:<7.0f}{s['mean_grounding_all']:.2f}")
    print(f"\nSaved corrected_comparison_report.{{md,json}}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
