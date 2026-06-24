"""FULL-dataset XGBoost baseline (no ablation).

Replicates evaluate.py's baseline section against the raw data in
data/raw/ciciot2023 (and data/raw/iot23 if it loads), but does NOT run the
ablation study, so it never touches the finalized ablation_results.json.
Writes data/eval/baseline_full_report.{md,json}.

Run: python scripts/run_baseline_full.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.services.feature_extraction.extract_ciciot import extract_ciciot
from src.services.feature_extraction.extract_iot23 import extract_iot23
from src.services.evaluation.baseline import train_xgboost_baseline, DEFAULT_FEATURE_COLS

CICIOT = Path("data/raw/ciciot2023")
IOT23 = Path("data/raw/iot23")
OUT_JSON = Path("data/eval/baseline_full_report.json")
OUT_MD = Path("data/eval/baseline_full_report.md")


def main():
    print("=" * 64)
    print("  FULL XGBoost Baseline (raw datasets, no ablation)")
    print("=" * 64)
    splits = {}

    if CICIOT.exists():
        t0 = time.time()
        try:
            splits["ciciot"] = extract_ciciot(CICIOT)
            print(f"  [OK] CICIoT: {len(splits['ciciot']['train']):,} train / "
                  f"{len(splits['ciciot']['test']):,} test  ({time.time()-t0:.0f}s)")
        except Exception as e:
            print(f"  [warn] CICIoT load failed: {type(e).__name__}: {str(e)[:120]}")
    else:
        print(f"  [warn] {CICIOT} not found")

    if IOT23.exists():
        t0 = time.time()
        try:
            splits["iot23"] = extract_iot23(IOT23)
            print(f"  [OK] IoT-23: {len(splits['iot23']['train']):,} train / "
                  f"{len(splits['iot23']['test']):,} test  ({time.time()-t0:.0f}s)")
        except Exception as e:
            print(f"  [warn] IoT-23 load failed: {type(e).__name__}: {str(e)[:120]}")

    if not splits:
        print("  [FAIL] No datasets loaded; cannot run baseline.")
        return 1

    train_df = pd.concat([s["train"] for s in splits.values()], ignore_index=True)
    test_df = pd.concat([s["test"] for s in splits.values()], ignore_index=True)
    used_feats = [c for c in DEFAULT_FEATURE_COLS if c in train_df.columns]
    print(f"\n  Combined: {len(train_df):,} train / {len(test_df):,} test")
    print(f"  Datasets: {list(splits.keys())}")
    print(f"  Features available to XGBoost: {len(used_feats)}")
    print(f"  Classes: {train_df['label'].nunique()}")

    print("\n  Training XGBoost (200 trees, depth 6)...")
    t0 = time.time()
    res = train_xgboost_baseline(train_df, test_df)
    print(f"  Trained in {time.time()-t0:.0f}s")

    print("\n  --- FULL BASELINE RESULTS ---")
    print(f"  Macro F1 : {res.macro_f1}")
    print(f"  AUC-ROC  : {res.auc_roc}")
    print(f"  n_train  : {res.n_train:,}   n_test: {res.n_test:,}   classes: {len(res.label_classes)}")
    top = sorted(res.feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
    print("  Top features:")
    for name, imp in top:
        print(f"     {name:<18} {imp:.4f}")

    payload = {
        "note": "FULL-dataset XGBoost baseline (no ablation). Mirrors evaluate.py "
                "baseline section over raw data.",
        "datasets": list(splits.keys()),
        "n_features": len(used_feats),
        "features_used": used_feats,
        "macro_f1": res.macro_f1,
        "auc_roc": res.auc_roc,
        "n_train": res.n_train,
        "n_test": res.n_test,
        "classes": res.label_classes,
        "per_class_f1": res.per_class_f1,
        "feature_importances": res.feature_importances,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = [
        "# XGBoost Baseline - FULL Dataset",
        "",
        f"Datasets: **{', '.join(splits.keys())}** (raw, no sampling). No ablation re-run.",
        "",
        "## Metrics",
        "",
        f"- **Macro F1:** {res.macro_f1}",
        f"- **AUC-ROC (OVR macro):** {res.auc_roc}",
        f"- **Train / Test:** {res.n_train:,} / {res.n_test:,}",
        f"- **Classes:** {len(res.label_classes)}",
        f"- **Features used:** {len(used_feats)}",
        "",
        "## Top feature importances",
        "",
        "| Feature | Importance |",
        "|---|---|",
    ]
    for name, imp in top:
        md.append(f"| {name} | {imp:.4f} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n  Saved: {OUT_JSON}\n  Saved: {OUT_MD}")
    print("=" * 64 + "\n  FULL BASELINE: DONE\n" + "=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
