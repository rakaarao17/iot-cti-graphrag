"""Give zeroday-phi3 its best shot: native format (39-feature CICIoT + short output).

The earlier classification test used Zeek-flow features (a different representation).
zeroday's Modelfile shows num_predict=8 (built to emit a short label). This test uses
the raw 39-feature CICIoT rows it was likely trained on, its phi3 chat template, and a
short output budget. If zeroday is a real classifier, accuracy should jump here.
Writes data/eval/zeroday_native_report.{md,json}. Ollama required.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests
import pandas as pd

RAW = Path("data/raw/ciciot2023")
MODELS = ["zeroday-phi3-ciciot-v2:latest", "phi3:latest"]
PER_FILE = 3
CHAT_URL = "http://localhost:11434/api/chat"
OPTS = {"temperature": 0.0, "num_predict": 24}
FILES = ["BenignTraffic", "DDoS-TCP_Flood", "DDoS-ICMP_Flood", "DDoS-SYN_Flood",
         "DDoS-UDP_Flood", "DNS_Spoofing", "Backdoor_Malware", "DictionaryBruteForce",
         "DDoS-SlowLoris", "BrowserHijacking"]


def clean_label(stem):
    n = stem.replace(".pcap", "").rstrip("-")
    return "Benign" if n == "BenignTraffic" else n


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def chat(model, prompt):
    r = requests.post(CHAT_URL, json={"model": model, "stream": False, "options": OPTS,
                                      "messages": [{"role": "user", "content": prompt}]}, timeout=120)
    return r.json().get("message", {}).get("content", "")


def main():
    labels = [clean_label(f) for f in FILES]
    cand = ", ".join(labels)
    rows = []
    flows = []
    for f in FILES:
        p = RAW / f"{f}.pcap.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p, nrows=200)
        feat_cols = [c for c in df.columns if c.strip().lower() != "label"]
        for _, r in df.sample(min(PER_FILE, len(df)), random_state=42).iterrows():
            feats = ", ".join(f"{c}={r[c]}" for c in feat_cols)
            flows.append((clean_label(f), feats))
    print(f"Native test: {len(flows)} flows x {len(MODELS)} models | 39-feature CICIoT format")

    t0 = time.time()
    summary = {}
    for model in MODELS:
        print(f"== {model} ==")
        correct = valid = 0
        for true, feats in flows:
            prompt = (f"Classify this CICIoT2023 network flow into exactly ONE attack type from: "
                      f"{cand}.\n\nFeatures: {feats}\n\nAttack type:")
            try:
                ans = chat(model, prompt).strip()
            except Exception:
                ans = ""
            na = norm(ans)
            is_valid = any(norm(l) in na or na in norm(l) for l in labels) if na else False
            is_correct = bool(na) and (norm(true) in na or na in norm(true))
            correct += is_correct; valid += is_valid
            rows.append({"model": model, "true": true, "pred": ans[:50],
                         "correct": is_correct, "valid": is_valid})
        n = len(flows)
        summary[model] = {"accuracy": round(correct/n, 3), "valid_label_rate": round(valid/n, 3), "n": n}
        print(f"   accuracy={correct/n:.2f}  valid_label={valid/n:.2f}  ({time.time()-t0:.0f}s)")

    Path("data/eval/zeroday_native_raw.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    Path("data/eval/zeroday_native_report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md = ["# zeroday Native-Format Classification Test", "",
          f"39-feature CICIoT representation + phi3 template + short output (its trained setup). "
          f"{len(flows)} flows.", "",
          "| Model | Accuracy | Valid-label rate |", "|-------|----------|------------------|"]
    for m in MODELS:
        s = summary[m]; md.append(f"| {m} | {s['accuracy']:.2f} | {s['valid_label_rate']:.2f} |")
    Path("data/eval/zeroday_native_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n=== SUMMARY ===")
    for m in MODELS:
        print(f"  {m:34s} acc={summary[m]['accuracy']:.2f}  valid={summary[m]['valid_label_rate']:.2f}")
    print(f"\nSaved zeroday_native_report.*  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    sys.exit(main())
