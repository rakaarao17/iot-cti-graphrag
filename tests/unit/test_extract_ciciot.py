import pandas as pd
import numpy as np
from src.services.feature_extraction.extract_ciciot import extract_ciciot, REQUIRED_COLUMNS


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_raw_flow_df(n=100):
    """Simulate the original raw-flow CICIoT format (src_ip/dst_ip/label columns)."""
    n_benign = int(n * 0.7)
    n_ddos = int(n * 0.2)
    n_dos = n - n_benign - n_ddos
    labels = ["Benign"] * n_benign + ["DDoS-TCP_Flood"] * n_ddos + ["DoS-SYN_Flood"] * n_dos
    return pd.DataFrame({
        "flow_id": range(n),
        "src_ip": ["192.168.1.1"] * n,
        "dst_ip": ["10.0.0.1"] * n,
        "src_port": [12345] * n,
        "dst_port": [80] * n,
        "protocol": [6] * n,
        "flow_duration": [0.1] * n,
        "tot_fwd_pkts": [5] * n,
        "tot_bwd_pkts": [3] * n,
        "totlen_fwd_pkts": [500] * n,
        "totlen_bwd_pkts": [300] * n,
        "label": labels,
    })


def make_pre_extracted_df(n=100):
    """Simulate the 39-feature pre-extracted CICIoT format (no IPs or label column)."""
    return pd.DataFrame({
        "Header_Length": np.random.randint(20, 60, n),
        "Protocol Type": np.random.randint(0, 256, n),
        "Time_To_Live": np.random.randint(1, 128, n),
        "Rate": np.random.uniform(0, 1000, n),
        "fin_flag_number": np.zeros(n),
        "syn_flag_number": np.ones(n),
        "rst_flag_number": np.zeros(n),
        "psh_flag_number": np.zeros(n),
        "ack_flag_number": np.ones(n),
        "ece_flag_number": np.zeros(n),
        "cwr_flag_number": np.zeros(n),
        "ack_count": np.random.randint(0, 10, n),
        "syn_count": np.random.randint(0, 10, n),
        "fin_count": np.zeros(n),
        "rst_count": np.zeros(n),
        "HTTP": np.zeros(n), "HTTPS": np.zeros(n), "DNS": np.zeros(n),
        "Telnet": np.zeros(n), "SMTP": np.zeros(n), "SSH": np.zeros(n),
        "IRC": np.zeros(n), "TCP": np.ones(n), "UDP": np.zeros(n),
        "DHCP": np.zeros(n), "ARP": np.zeros(n), "ICMP": np.zeros(n),
        "IGMP": np.zeros(n), "IPv": np.ones(n), "LLC": np.zeros(n),
        "Tot sum": np.random.uniform(0, 10000, n),
        "Min": np.random.uniform(0, 100, n),
        "Max": np.random.uniform(100, 1000, n),
        "AVG": np.random.uniform(50, 500, n),
        "Std": np.random.uniform(0, 100, n),
        "Tot size": np.random.uniform(0, 50000, n),
        "IAT": np.random.uniform(0, 1, n),
        "Number": np.random.randint(1, 100, n),
        "Variance": np.random.uniform(0, 1000, n),
    })


# ── Raw-flow format tests ─────────────────────────────────────────────────────

def test_raw_flow_returns_train_test_split(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)

    assert "train" in result
    assert "test" in result
    assert len(result["train"]) == 80
    assert len(result["test"]) == 20


def test_raw_flow_output_has_required_columns(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)

    for col in REQUIRED_COLUMNS:
        assert col in result["train"].columns, f"Missing column: {col}"


def test_raw_flow_dataset_column_is_ciciot(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(50).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    assert (result["train"]["dataset"] == "ciciot2023").all()


def test_raw_flow_no_test_rows_in_train(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    train_uids = set(result["train"]["uid"])
    test_uids = set(result["test"]["uid"])
    assert train_uids.isdisjoint(test_uids), "Train and test sets overlap"


# ── Pre-extracted format tests ────────────────────────────────────────────────

def test_pre_extracted_detects_format_from_columns(tmp_path):
    """Files with Header_Length / Protocol Type trigger the pre-extracted path."""
    csv_file = tmp_path / "DDoS-TCP_Flood.pcap.csv"
    make_pre_extracted_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    assert "train" in result and "test" in result


def test_pre_extracted_label_derived_from_filename(tmp_path):
    """Label is the filename stem without .pcap suffix."""
    (tmp_path / "DDoS-TCP_Flood.pcap.csv").write_bytes(
        make_pre_extracted_df(50).to_csv(index=False).encode()
    )
    (tmp_path / "BenignTraffic.pcap.csv").write_bytes(
        make_pre_extracted_df(50).to_csv(index=False).encode()
    )

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    labels = set(result["train"]["label"]) | set(result["test"]["label"])
    assert "DDoS-TCP_Flood" in labels
    assert "Benign" in labels
    assert "BenignTraffic" not in labels  # must be normalized


def test_pre_extracted_has_required_columns(tmp_path):
    csv_file = tmp_path / "DDoS-UDP_Flood.pcap.csv"
    make_pre_extracted_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    for col in REQUIRED_COLUMNS:
        assert col in result["train"].columns, f"Missing required column: {col}"


def test_pre_extracted_keeps_feature_columns(tmp_path):
    """All 39 original feature columns should survive into the output."""
    csv_file = tmp_path / "Recon-PortScan.pcap.csv"
    make_pre_extracted_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    # Normalized column names (lowercase, underscore)
    assert "header_length" in result["train"].columns
    assert "time_to_live" in result["train"].columns
    assert "variance" in result["train"].columns


def test_pre_extracted_dataset_column_is_ciciot(tmp_path):
    csv_file = tmp_path / "Mirai-greeth_flood.pcap.csv"
    make_pre_extracted_df(60).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    assert (result["train"]["dataset"] == "ciciot2023").all()


def test_pre_extracted_no_overlap_train_test(tmp_path):
    csv_file = tmp_path / "DoS-SYN_Flood.pcap.csv"
    make_pre_extracted_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    train_uids = set(result["train"]["uid"])
    test_uids = set(result["test"]["uid"])
    assert train_uids.isdisjoint(test_uids)


# ── Backward-compatible aliases (old test names) ──────────────────────────────

def test_extract_ciciot_returns_train_test_split(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(100).to_csv(csv_file, index=False)
    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    assert len(result["train"]) == 80 and len(result["test"]) == 20


def test_extract_ciciot_output_has_required_columns(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(100).to_csv(csv_file, index=False)
    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    for col in REQUIRED_COLUMNS:
        assert col in result["train"].columns


def test_extract_ciciot_dataset_column_is_ciciot(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(50).to_csv(csv_file, index=False)
    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    assert (result["train"]["dataset"] == "ciciot2023").all()


def test_extract_ciciot_no_test_rows_in_train(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_raw_flow_df(100).to_csv(csv_file, index=False)
    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    assert set(result["train"]["uid"]).isdisjoint(set(result["test"]["uid"]))
