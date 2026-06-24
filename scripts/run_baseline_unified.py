"""XGBoost baseline on the UNIFIED processed dataset (CICIoT + IoT-23).

Uses data/processed/unified_features.csv (the Zeek-flow feature table the
knowledge graph is built from), so this baseline is the fairest head-to-head
against the GraphRAG approach (same data + feature schema). This is DISTINCT
from baseline_full_report (which used CICIoT's 46 pre-extracted features).

Note: IoT-23 rows in this dataset are all label=Benign, so they add Benign
volume but no new attack classes. Writes baseline_unified_report.{md,json}.

Run: python scripts/run_baseline_unified.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sklearn.model_selection import train_test_split

from src.services.evaluation.baseline import train_xgboost_baseline

SRC = Path("data/processed/unified_features.csv")
OUT_JSON = Path("data/eval/baseline_unified_report.json")
OUT_MD = Path("data/eval/baseline_unified_report.md")

FEATURES = [
    "duration", "src_port", "dst_port",
    "orig_bytes", "resp_bytes", "orig_pkts", "resp_pkts",
    "bytes_ratio", "packet_ratio", "bytes_per_pkt",
]


def main():
    print("=" * 64)
    print("  UNIFIED XGBoost Baseline (CICIoT + IoT-23, Zeek-flow features)")
    print("=" * 64)
    t0 = time.time()
    df = pd.read_csv(SRC, low_memory=False)
    print(f"  Loaded {len(df):,} rows in {time.time()-t0:.0f}s")
    print(f"  By dataset: {df['dataset'].value_counts().to_dict()}")

    counts = df["label"].value_counts()
    keep = counts[counts >= 10].index
    df = df[df["label"].isin(keep)].copy()
    feats = [c for c in FEATURES if c in df.columns]
    print(f"  Features: {feats}")
    print(f"  Classes: {df['label'].nunique()}")

    # NOTE: a single-shot fit on all 5.5M rows collapses to a degenerate near-random
    # model (Macro-F1 ~0.05, AUC ~0.51) -- an XGBoost training pathology at that scale.
    # A size sweep shows the learning curve has already converged by ~1M rows
    # (200k: F1 0.255/AUC 0.903; 1M: F1 0.262/AUC 0.907), so we train on a
    # representative stratified sample. This is the reported unified baseline.
    MAX_ROWS = 1_500_000
    sampled = False
    if len(df) > MAX_ROWS:
        df, _ = train_test_split(
            df, train_size=MAX_ROWS, random_state=42, stratify=df["label"])
        sampled = True
        print(f"  Subsampled to {len(df):,} rows (stratified) -- full-set run is degenerate; "
              f"curve converged by 1M")

    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label"])
    print(f"  Train: {len(train_df):,}  Test: {len(test_df):,}")

    print("\n  Training XGBoost (200 trees, depth 6)...")
    t0 = time.time()
    res = train_xgboost_baseline(train_df, test_df, feature_cols=feats)
    print(f"  Trained in {time.time()-t0:.0f}s")

    print("\n  --- UNIFIED BASELINE RESULTS ---")
    print(f"  Macro F1 : {res.macro_f1}")
    print(f"  AUC-ROC  : {res.auc_roc}")
    print(f"  n_train  : {res.n_train:,}   n_test: {res.n_test:,}   classes: {len(res.label_classes)}")
    top = sorted(res.feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
    for name, imp in top:
        print(f"     {name:<16} {imp:.4f}")

    payload = {
        "note": "UNIFIED baseline on data/processed/unified_features.csv "
                "(CICIoT+IoT-23, Zeek-flow features). Fairest comparison vs the "
                "graph. IoT-23 rows are all Benign. Distinct from baseline_full "
                "(46 pre-extracted CICIoT features).",
        "trained_on_stratified_sample": sampled,
        "full_set_degenerate_note": "Single-shot fit on all 5.5M rows yields a "
                "degenerate near-random model (F1~0.05, AUC~0.51). Size sweep "
                "(200k: 0.255/0.903; 1M: 0.262/0.907) shows convergence, so a "
                "1.5M stratified sample is used as the representative baseline.",
        "source": str(SRC),
        "by_dataset": {k: int(v) for k, v in df["dataset"].value_counts().items()},
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
        "# XGBoost Baseline - UNIFIED (CICIoT + IoT-23)",
        "",
        "> Trained on a stratified sample of `data/processed/unified_features.csv` "
        f"({res.n_train + res.n_test:,} of 5.5M rows) using the Zeek-flow feature "
        "schema the knowledge graph is built from -- the fairest head-to-head vs "
        "GraphRAG. IoT-23 rows are all `Benign`. **Distinct** from "
        "`baseline_full_report` (CICIoT 46 pre-extracted features).",
        "",
        "> **Why a sample:** a single-shot XGBoost fit on all 5.5M rows collapses to "
        "a degenerate near-random model (F1~0.05, AUC~0.51). A size sweep "
        "(200k -> 0.255/0.903, 1M -> 0.262/0.907) shows the learning curve has "
        "converged, so a 1.5M stratified sample is the representative baseline.",
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
    print(f"\n  Saved: {OUT_JSON}\n  Saved: {OUT_MD}")
    print("=" * 64 + "\n  UNIFIED BASELINE: DONE\n" + "=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
