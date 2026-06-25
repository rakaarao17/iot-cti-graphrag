"""Readable 3-model comparison on the SAME real retrieved contexts.

Purpose: judge model quality by READING outputs, not by trusting grounding or a
coherence heuristic. For each of N representative queries it runs all three local
models in two modes:
  - generate : raw /api/generate with a plain prompt (what the system does today)
  - chat     : /api/chat, which applies each model's own prompt template
The second mode tests whether the fine-tuned model's gibberish is a prompt-format
confound rather than a quality problem.

Writes data/eval/model_readout.md (full text, human-readable) + model_readout.json.
Run: python scripts/run_model_readout.py   (Ollama required; Neo4j not needed)
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.services.threat_explanation.grounding import check_grounding

MODELS = ["phi3:latest", "zeroday-phi3-ciciot-v2:latest", "gemma4:e2b"]
N_QUERIES = 8
ABL = Path("data/eval/ablation_results.json")
OUT_MD = Path("data/eval/model_readout.md")
OUT_JSON = Path("data/eval/model_readout.json")
GEN_URL = "http://localhost:11434/api/generate"
CHAT_URL = "http://localhost:11434/api/chat"
OPTS = {"temperature": 0.3, "num_predict": 4096}

PROMPT = ("You are an IoT cybersecurity analyst. Using ONLY the retrieved context below, "
          "answer the question factually and concisely, citing specific entities "
          "(IPs, attack names, MITRE IDs, counts) from the context.\n\n"
          "Retrieved context:\n{context}\n\nQuestion: {query}\n\nAnswer:")


def coherence(text):
    words = re.findall(r"[A-Za-z]{2,}", text)
    if not words:
        return 0.0
    real = sum(1 for w in words if re.search(r"[aeiou]", w.lower()) and len(w) <= 18)
    junk = sum(1 for w in words if len(w) > 18)
    return round(max(0.0, real / len(words) - junk / len(words)), 3)


def gen_raw(model, prompt):
    r = requests.post(GEN_URL, json={"model": model, "prompt": prompt, "stream": False,
                                     "options": OPTS}, timeout=600)
    return r.json().get("response", "")


def gen_chat(model, prompt):
    r = requests.post(CHAT_URL, json={"model": model, "stream": False, "options": OPTS,
                                      "messages": [{"role": "user", "content": prompt}]}, timeout=600)
    return r.json().get("message", {}).get("content", "")


def main():
    recs = [r for r in json.load(open(ABL, encoding="utf-8")) if r["condition"] == "combined"]
    step = max(1, len(recs) // N_QUERIES)
    picks = recs[::step][:N_QUERIES]
    print(f"Readout: {len(picks)} queries x {len(MODELS)} models x 2 modes "
          f"= {len(picks)*len(MODELS)*2} generations")

    md = ["# Readable 3-Model Comparison (same real contexts)", "",
          "Two modes per model: **generate** (raw prompt, current system path) and "
          "**chat** (model's own prompt template). Read the answers; the metrics are "
          "secondary. `grounding` = answer-entities in context; `coh` = coherence heuristic.", ""]
    data = []
    t0 = time.time()
    for qi, rec in enumerate(picks, 1):
        ctx = rec.get("context_text", "")
        prompt = PROMPT.format(context=ctx[:6000], query=rec["query"])
        md += [f"## Q{qi}: {rec['query']}", ""]
        print(f"\n[Q{qi}] {rec['query'][:70]}")
        for model in MODELS:
            for mode, fn in [("generate", gen_raw), ("chat", gen_chat)]:
                t = time.time()
                try:
                    ans = fn(model, prompt)
                except Exception as e:
                    ans = f"<ERROR: {e}>"
                dt = time.time() - t
                g = check_grounding(ans, ctx).grounding_ratio if ans and not ans.startswith("<ERROR") else 0.0
                coh = coherence(ans)
                toks = len(ans.split())
                data.append({"q": qi, "model": model, "mode": mode, "grounding": round(g, 3),
                             "coherence": coh, "tokens": toks, "latency_s": round(dt, 1)})
                print(f"   {model:32s} {mode:8s} g={g:.2f} coh={coh:.2f} tok={toks} ({dt:.0f}s)")
                md += [f"**{model} - {mode}**  (grounding={g:.2f}, coh={coh:.2f}, tokens={toks})", "",
                       "```", ans.strip()[:1500] if ans else "(empty)", "```", ""]
        md += ["---", ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # compact summary table (mean per model x mode)
    import numpy as np
    print("\n=== SUMMARY (mean over queries) ===")
    print(f"{'model':34s}{'mode':9s}{'grounding':11s}{'coherence':11s}{'tokens'}")
    for model in MODELS:
        for mode in ["generate", "chat"]:
            sub = [d for d in data if d["model"] == model and d["mode"] == mode]
            if sub:
                g = np.mean([d["grounding"] for d in sub]); c = np.mean([d["coherence"] for d in sub])
                tk = np.mean([d["tokens"] for d in sub])
                print(f"{model:34s}{mode:9s}{g:<11.3f}{c:<11.3f}{tk:.0f}")
    print(f"\nSaved: {OUT_MD} (READ THIS), {OUT_JSON}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
