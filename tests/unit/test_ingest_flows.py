import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
from src.services.knowledge_graph.ingest_flows import ingest_flows, build_flow_batch


def make_flows(n=10):
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
        "label": ["Benign"] * 8 + ["DDoS-TCP_Flood"] * 2,
        "dataset": ["ciciot2023"] * n,
    })


def test_build_flow_batch_produces_correct_dict():
    flows = make_flows(10)
    batch = build_flow_batch(flows)
    assert len(batch) == 10
    assert batch[0]["uid"] == "uid_0"
    assert batch[0]["src_ip"] == "192.168.1.1"
    assert batch[0]["label"] == "Benign"


def test_ingest_flows_calls_batch_query(tmp_path):
    flows = make_flows(10)
    with patch("src.services.knowledge_graph.ingest_flows.run_batch_query") as mock_batch:
        mock_batch.return_value = None
        ingest_flows(flows, batch_size=3)
        # Should be called at least twice: batches of 3,3,3,1
        assert mock_batch.call_count >= 2
