import pandas as pd
import pytest
from src.services.evaluation.baseline import train_xgboost_baseline, BaselineResult

NUMERIC_FEATURES = ["duration", "fwd_pkts", "bwd_pkts", "fwd_bytes", "bwd_bytes"]


def make_flows(n=200, seed=42):
    import numpy as np
    rng = np.random.default_rng(seed)
    labels = (["Benign"] * (n // 2)) + (["DDoS-TCP_Flood"] * (n // 2))
    return pd.DataFrame({
        "duration": rng.uniform(0, 10, n),
        "fwd_pkts": rng.integers(1, 100, n),
        "bwd_pkts": rng.integers(0, 50, n),
        "fwd_bytes": rng.uniform(100, 10000, n),
        "bwd_bytes": rng.uniform(0, 5000, n),
        "label": labels,
    })


def test_baseline_returns_result_object():
    df = make_flows(200)
    train = df.iloc[:160]
    test = df.iloc[160:]
    result = train_xgboost_baseline(train, test, feature_cols=NUMERIC_FEATURES)
    assert isinstance(result, BaselineResult)


def test_baseline_macro_f1_in_valid_range():
    df = make_flows(200)
    train, test = df.iloc[:160], df.iloc[160:]
    result = train_xgboost_baseline(train, test, feature_cols=NUMERIC_FEATURES)
    assert 0.0 <= result.macro_f1 <= 1.0


def test_baseline_has_per_class_scores():
    df = make_flows(200)
    train, test = df.iloc[:160], df.iloc[160:]
    result = train_xgboost_baseline(train, test, feature_cols=NUMERIC_FEATURES)
    assert "Benign" in result.per_class_f1
    assert "DDoS-TCP_Flood" in result.per_class_f1
