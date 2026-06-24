"""XGBoost baseline on the bundled CICIoT2023 SAMPLE.

NOTE: This trains on data/samples/ciciot2023_sample.csv (24,996 rows), NOT the
full dataset. The full-dataset 39-feature baseline requires the raw data in
data/raw/ciciot2023 (gitignored, not present here). This sample baseline is
clearly labeled as such and written to a dedicated report file so it is never
confused with the ablation / full-pipeline results.

Run: python scripts/run_baseline_sample.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sklearn.model_selection import train_test_split

from src.services.evaluation.baseline import train_xgboost_baseline

SAMPLE = Path("data/samples/ciciot2023_sample.csv")
OUT_JSON = Path("data/eval/baseline_sample_report.json")
OUT_MD = Path("data/eval/baseline_sample_report.md")

# Real numeric features that exist in the sample (no fabrication).
FEATURES = [
    "duration", "src_port", "dst_port",
    "orig_bytes", "resp_bytes", "orig_pkts", "resp_pkts",
    "bytes_ratio", "packet_ratio", "bytes_per_pkt",
]


def main():
    print("=" * 64)
    print("  XGBoost Baseline - CICIoT2023 SAMPLE (not full dataset)")
    print("=" * 64)
    df = pd.read_csv(SAMPLE)
    print(f"  Loaded {len(df):,} rows, {df.shape[1]} columns from {SAMPLE.name}")

    # Drop ultra-rare classes that cannot be stratified (<2 rows)
    counts = df["label"].value_counts()
    keep = counts[counts >= 2].index
    df = df[df["label"].isin(keep)].copy()

    feats = [c for c in FEATURES if c in df.columns]
    print(f"  Using {len(feats)} features: {feats}")
    print(f"  Classes: {df['label'].nunique()}")

    try:
        train_df, test_df = train_test_split(
            df, test_size=0.2, random_state=42, stratify=df["label"])
    except ValueError:
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

    print(f"  Train: {len(train_df):,}  Test: {len(test_df):,}")
    print("\n  Training XGBoost (200 trees, depth 6)...")
    res = train_xgboost_baseline(train_df, test_df, feature_cols=feats)

    print("\n  --- RESULTS (sample-based) ---")
    print(f"  Macro F1 : {res.macro_f1}")
    print(f"  AUC-ROC  : {res.auc_roc}")
    print(f"  n_train  : {res.n_train:,}   n_test: {res.n_test:,}   classes: {len(res.label_classes)}")
    top = sorted(res.feature_importances.items(), key=lambda x: x[1], reverse=True)[:8]
    print("  Top features:")
    for name, imp in top:
        print(f"     {name:<16} {imp:.4f}")

    payload = {
        "note": "SAMPLE-BASED baseline on data/samples/ciciot2023_sample.csv; "
                "NOT the full-dataset 39-feature baseline (raw data not present).",
        "source": str(SAMPLE),
        "features_used": feats,
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
        "# XGBoost Baseline - CICIoT2023 SAMPLE",
        "",
        "> **Sample-based.** Trained on `data/samples/ciciot2023_sample.csv` "
        f"({res.n_train + res.n_test:,} rows). This is NOT the full-dataset "
        "39-feature baseline, which requires the raw CICIoT2023 data in "
        "`data/raw/ciciot2023` (not present in this checkout).",
        "",
        "## Metrics",
        "",
        f"- **Macro F1:** {res.macro_f1}",
        f"- **AUC-ROC (OVR macro):** {res.auc_roc}",
        f"- **Train / Test:** {res.n_train:,} / {res.n_test:,}",
        f"- **Classes:** {len(res.label_classes)}",
        f"- **Features ({len(feats)}):** {', '.join(feats)}",
        "",
        "## Top feature importances",
        "",
        "| Feature | Importance |",
        "|---|---|",
    ]
    for name, imp in top:
        md.append(f"| {name} | {imp:.4f} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"\n  Saved: {OUT_JSON}")
    print(f"  Saved: {OUT_MD}")
    print("\n" + "=" * 64)
    print("  BASELINE (SAMPLE): DONE")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
