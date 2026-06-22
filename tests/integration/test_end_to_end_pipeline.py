"""End-to-end integration test using a tiny synthetic dataset (no real data required)."""
import pytest
import pandas as pd


def make_tiny_dataset(n=20):
    benign_count = int(n * 0.75)
    attack_count = n - benign_count
    return pd.DataFrame({
        "uid": [f"uid_{i}" for i in range(n)],
        "src_ip": ["192.168.1.1"] * n,
        "dst_ip": ["10.0.0.1"] * n,
        "src_port": [12345] * n,
        "dst_port": [80] * n,
        "protocol": ["tcp"] * n,
        "duration": [0.1] * n,
        "fwd_pkts": [5] * n,
        "bwd_pkts": [3] * n,
        "fwd_bytes": [500.0] * n,
        "bwd_bytes": [300.0] * n,
        "label": ["Benign"] * benign_count + ["DDoS-TCP_Flood"] * attack_count,
        "dataset": ["ciciot2023"] * n,
    })


def test_baseline_runs_on_synthetic_data():
    from src.services.evaluation.baseline import train_xgboost_baseline, DEFAULT_FEATURE_COLS
    df = make_tiny_dataset(100)
    train, test = df.iloc[:80], df.iloc[80:]
    assert all(c in df.columns for c in DEFAULT_FEATURE_COLS), (
        f"Dataset is missing expected feature columns: "
        f"{[c for c in DEFAULT_FEATURE_COLS if c not in df.columns]}"
    )
    result = train_xgboost_baseline(train, test)
    assert 0.0 <= result.macro_f1 <= 1.0


def test_classification_metrics_run_on_synthetic_labels():
    from src.services.evaluation.classification_metrics import compute_classification_metrics
    y_true = ["Benign", "DDoS-TCP_Flood", "Benign"]
    y_pred = ["Benign", "DDoS-TCP_Flood", "DDoS-TCP_Flood"]
    result = compute_classification_metrics(y_true, y_pred)
    assert result.macro_f1 >= 0.0


def test_grounding_check_runs_on_synthetic_text():
    from src.services.threat_explanation.grounding import check_grounding
    result = check_grounding(
        "Device 192.168.1.1 used DDoS attack",
        "Device at 192.168.1.1 was classified as DDoS"
    )
    assert result.grounding_ratio > 0.0
