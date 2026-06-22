import io
import pytest
import pandas as pd
from pathlib import Path
from src.services.feature_extraction.extract_iot23 import (
    extract_iot23, parse_zeek_conn_log, align_labels, REQUIRED_COLUMNS
)


SAMPLE_CONN_LOG = """\
#separator \\x09
#set_separator\t,
#empty_field\t(empty)
#unset_field\t-
#path\tconn
#open\t2018-12-21-11-23-45
#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\tduration\torig_bytes\tresp_bytes
#types\ttime\tstring\taddr\tport\taddr\tport\tenum\tinterval\tcount\tcount
1545389025.123456\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\t0.123\t500\t300
1545389026.234567\tCdef456\t192.168.1.195\t12346\t23.45.67.89\t443\ttcp\t0.456\t1000\t800
"""

SAMPLE_LABEL = """\
1545389025.123456\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\tMirai\t-\t-
1545389026.234567\tCdef456\t192.168.1.195\t12346\t23.45.67.89\t443\ttcp\tBenign\t-\t-
"""


def test_parse_zeek_conn_log(tmp_path):
    log_file = tmp_path / "conn.log"
    log_file.write_text(SAMPLE_CONN_LOG)
    df = parse_zeek_conn_log(log_file)
    assert len(df) == 2
    assert "uid" in df.columns
    assert df["uid"].tolist() == ["Cabc123", "Cdef456"]


def test_align_labels_matches_by_uid():
    flows = pd.DataFrame({
        "uid": ["Cabc123", "Cdef456"],
        "src_ip": ["192.168.1.195", "192.168.1.195"],
    })
    label_lines = [
        "1545389025.0\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\tMirai\t-\t-",
        "1545389026.0\tCdef456\t192.168.1.195\t12346\t23.45.67.89\t443\ttcp\tBenign\t-\t-",
    ]
    labeled = align_labels(flows, label_lines)
    assert labeled["label"].tolist() == ["Mirai", "Benign"]


def test_align_labels_drops_unlabeled_rows():
    flows = pd.DataFrame({
        "uid": ["Cabc123", "Cunknown"],
        "src_ip": ["192.168.1.195", "192.168.1.195"],
    })
    label_lines = [
        "1545389025.0\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\tMirai\t-\t-",
    ]
    labeled = align_labels(flows, label_lines)
    assert len(labeled) == 1
    assert labeled["uid"].iloc[0] == "Cabc123"


def test_extract_iot23_returns_train_test(tmp_path):
    scenario_dir = tmp_path / "CTU-IoT-Malware-Capture-1-1"
    scenario_dir.mkdir()
    (scenario_dir / "conn.log").write_text(SAMPLE_CONN_LOG)
    (scenario_dir / "conn.log.labeled").write_text(SAMPLE_LABEL)

    result = extract_iot23(data_dir=tmp_path, test_size=0.5, random_state=42)
    assert "train" in result and "test" in result
    assert len(result["train"]) + len(result["test"]) == 2
