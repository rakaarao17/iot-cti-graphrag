"""Per-class classification metrics for attack detection evaluation."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from sklearn.metrics import f1_score, classification_report


@dataclass
class ClassificationResult:
    macro_f1: float
    weighted_f1: float
    per_class: Dict[str, Dict[str, float]]
    support: Dict[str, int]
    auc_roc: Optional[float] = None


def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
) -> ClassificationResult:
    """Compute per-class and macro-average F1 scores."""
    unique_labels = labels or sorted(set(y_true))

    macro_f1 = f1_score(y_true, y_pred, average="macro", labels=unique_labels, zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", labels=unique_labels, zero_division=0)

    report = classification_report(
        y_true, y_pred, labels=unique_labels, output_dict=True, zero_division=0
    )
    per_class = {
        lbl: {
            "f1": round(report[lbl]["f1-score"], 4),
            "precision": round(report[lbl]["precision"], 4),
            "recall": round(report[lbl]["recall"], 4),
        }
        for lbl in unique_labels if lbl in report
    }
    support = {lbl: int(report[lbl]["support"]) for lbl in unique_labels if lbl in report}

    return ClassificationResult(
        macro_f1=round(macro_f1, 4),
        weighted_f1=round(weighted_f1, 4),
        per_class=per_class,
        support=support,
    )
