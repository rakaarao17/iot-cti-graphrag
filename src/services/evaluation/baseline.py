"""XGBoost tabular baseline for comparison against graph-based approach."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

DEFAULT_FEATURE_COLS = [
    # Raw-flow features (available from both formats)
    "duration", "fwd_pkts", "bwd_pkts", "fwd_bytes", "bwd_bytes",
    "src_port", "dst_port",
    # Pre-extracted CICIoT 39-feature columns (present when using that format)
    "header_length", "protocol_type", "time_to_live", "rate",
    "fin_flag_number", "syn_flag_number", "rst_flag_number",
    "psh_flag_number", "ack_flag_number", "ece_flag_number", "cwr_flag_number",
    "ack_count", "syn_count", "fin_count", "rst_count",
    "http", "https", "dns", "telnet", "smtp", "ssh", "irc", "tcp", "udp",
    "dhcp", "arp", "icmp", "igmp", "ipv", "llc",
    "tot_sum", "min", "max", "avg", "std", "tot_size", "iat", "number", "variance",
]


@dataclass
class BaselineResult:
    macro_f1: float
    per_class_f1: Dict[str, float]
    auc_roc: Optional[float]
    feature_importances: Dict[str, float]
    n_train: int
    n_test: int
    label_classes: List[str] = field(default_factory=list)


def train_xgboost_baseline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str] = DEFAULT_FEATURE_COLS,
    label_col: str = "label",
) -> BaselineResult:
    """
    Train XGBoost on tabular features and evaluate on test split.

    Uses the same train/test split as the graph pipeline to ensure
    fair comparison. Reports macro-F1 and per-class F1 scores.
    """
    available_features = [c for c in feature_cols if c in train_df.columns]

    # Replace inf/-inf (e.g. from divide-by-zero in rate/ratio features) with NaN
    # so the fillna(0) below catches them; raw inf crashes XGBoost's DMatrix.
    X_train = train_df[available_features].replace([np.inf, -np.inf], np.nan).fillna(0).values
    y_train_raw = train_df[label_col].values

    X_test = test_df[available_features].replace([np.inf, -np.inf], np.nan).fillna(0).values
    y_test_raw = test_df[label_col].values

    le = LabelEncoder()
    y_train = le.fit_transform(y_train_raw)
    y_test = le.transform(y_test_raw)
    classes = list(le.classes_)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    report = classification_report(
        y_test, y_pred, target_names=classes, output_dict=True, zero_division=0
    )
    per_class = {cls: report[cls]["f1-score"] for cls in classes if cls in report}

    # AUC-ROC (OVR for multiclass; falls back to None if only 1 class in test)
    try:
        y_proba = model.predict_proba(X_test)
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
    except Exception:
        auc = None

    importances = {
        available_features[i]: float(model.feature_importances_[i])
        for i in range(len(available_features))
    }

    return BaselineResult(
        macro_f1=round(macro_f1, 4),
        per_class_f1=per_class,
        auc_roc=round(auc, 4) if auc is not None else None,
        feature_importances=importances,
        n_train=len(X_train),
        n_test=len(X_test),
        label_classes=classes,
    )
