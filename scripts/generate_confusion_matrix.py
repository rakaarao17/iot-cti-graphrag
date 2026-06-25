"""Confusion matrix for the full CICIoT XGBoost baseline (real predictions).

Retrains the full baseline (same params as baseline_full) to obtain test-set
predictions, then writes a row-normalized 34x34 confusion-matrix figure plus the
top off-diagonal confusions. CPU-only. Run: python scripts/generate_confusion_matrix.py
"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, f1_score
from xgboost import XGBClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.services.feature_extraction.extract_ciciot import extract_ciciot
from src.services.evaluation.baseline import DEFAULT_FEATURE_COLS

OUT = Path("results"); OUT.mkdir(exist_ok=True)


def main():
    print("Loading full CICIoT2023 (this is the ~30-min part)...")
    splits = extract_ciciot(Path("data/raw/ciciot2023"))
    tr, te = splits["train"], splits["test"]
    feats = [c for c in DEFAULT_FEATURE_COLS if c in tr.columns]
    Xtr = tr[feats].replace([np.inf, -np.inf], np.nan).fillna(0).values
    Xte = te[feats].replace([np.inf, -np.inf], np.nan).fillna(0).values
    le = LabelEncoder(); ytr = le.fit_transform(tr["label"]); yte = le.transform(te["label"])
    classes = list(le.classes_)
    print(f"  train={len(Xtr):,} test={len(Xte):,} classes={len(classes)} feats={len(feats)}")

    print("Training XGBoost...")
    m = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                      eval_metric="mlogloss", random_state=42, n_jobs=-1)
    m.fit(Xtr, ytr)
    yp = m.predict(Xte)
    print(f"  macro-F1 = {f1_score(yte, yp, average='macro'):.4f}")

    cm = confusion_matrix(yte, yp, normalize="true")
    fig, ax = plt.subplots(figsize=(13, 11))
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes))); ax.set_xticklabels(classes, rotation=90, fontsize=6)
    ax.set_yticks(range(len(classes))); ax.set_yticklabels(classes, fontsize=6)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("Full XGBoost baseline - row-normalized confusion matrix (34 classes)",
                 fontweight="bold")
    fig.colorbar(im, ax=ax, fraction=0.046, label="fraction of true class")
    fig.tight_layout()
    fig.savefig(OUT / "fig_confusion_matrix.png", dpi=300, bbox_inches="tight"); plt.close(fig)
    print("  [OK] results/fig_confusion_matrix.png")

    # top off-diagonal confusions
    conf = []
    for i in range(len(classes)):
        for j in range(len(classes)):
            if i != j and cm[i, j] > 0.05:
                conf.append((classes[i], classes[j], round(float(cm[i, j]), 3)))
    conf.sort(key=lambda x: -x[2])
    Path("data/eval/confusion_top.json").write_text(
        json.dumps({"macro_f1": float(f1_score(yte, yp, average='macro')),
                    "top_confusions": conf[:25]}, indent=2), encoding="utf-8")
    print("  Top confusions:")
    for a, b, v in conf[:8]:
        print(f"    {a} -> {b}: {v}")


if __name__ == "__main__":
    main()
