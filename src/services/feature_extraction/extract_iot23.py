"""IoT-23 feature extraction with Zeek log parsing and label alignment."""

from pathlib import Path
from typing import Dict, List

import pandas as pd
from sklearn.model_selection import train_test_split

from src.services.feature_extraction.extract_ciciot import REQUIRED_COLUMNS  # re-exported for callers

_ZEEK_FIELD_MAP = {
    "ts":          "timestamp",
    "uid":         "uid",
    "id.orig_h":   "src_ip",
    "id.orig_p":   "src_port",
    "id.resp_h":   "dst_ip",
    "id.resp_p":   "dst_port",
    "proto":       "protocol",
    "duration":    "duration",
    "orig_bytes":  "fwd_bytes",
    "resp_bytes":  "bwd_bytes",
}

# Known IoT-23 device IPs (from dataset documentation)
_DEVICE_IPS = {
    "192.168.1.195", "192.168.1.196", "192.168.1.197",
    "192.168.1.198", "192.168.1.199", "192.168.1.200",
}


def parse_zeek_conn_log(log_path: Path) -> pd.DataFrame:
    """
    Parse a Zeek conn.log file into a DataFrame.

    Handles Zeek's TSV format with #fields header line.
    Replaces '-' (Zeek null) with NaN.
    """
    fields: List[str] = []
    rows: List[dict] = []

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#fields"):
                fields = line.split("\t")[1:]
            elif line.startswith("#"):
                continue
            elif fields:
                values = line.split("\t")
                if len(values) != len(fields):
                    continue
                row = {
                    fields[i]: (None if values[i] == "-" else values[i])
                    for i in range(len(fields))
                }
                rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.rename(columns={k: v for k, v in _ZEEK_FIELD_MAP.items() if k in df.columns})

    if "src_port" in df.columns:
        df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce").fillna(0).astype(int)
    if "dst_port" in df.columns:
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").fillna(0).astype(int)
    if "duration" in df.columns:
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0.0)
    if "fwd_bytes" in df.columns:
        df["fwd_bytes"] = pd.to_numeric(df["fwd_bytes"], errors="coerce").fillna(0.0)
    if "bwd_bytes" in df.columns:
        df["bwd_bytes"] = pd.to_numeric(df["bwd_bytes"], errors="coerce").fillna(0.0)

    # IoT-23 does not provide per-packet counts in conn.log -- set to 0
    df["fwd_pkts"] = 0
    df["bwd_pkts"] = 0

    return df


def align_labels(flows: pd.DataFrame, label_lines: List[str]) -> pd.DataFrame:
    """
    Match flow rows to labels using UID (primary key).

    The IoT-23 label files use the same UID as Zeek conn.log.
    Rows with no matching label are dropped (conservative approach).
    """
    uid_to_label: dict = {}
    for line in label_lines:
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 8:
            uid = parts[1].strip()
            label = parts[7].strip()
            if uid and label and label != "-":
                uid_to_label[uid] = label

    if not uid_to_label:
        return flows.assign(label="Unknown")

    flows = flows.copy()
    flows["label"] = flows["uid"].map(uid_to_label)
    return flows.dropna(subset=["label"]).reset_index(drop=True)


def extract_iot23(
    data_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Extract and normalize IoT-23 flows with label alignment and train/test split.

    Scans `data_dir` for subdirectories containing conn.log + conn.log.labeled.
    Returns {"train": DataFrame, "test": DataFrame} with REQUIRED_COLUMNS schema.
    """
    data_dir = Path(data_dir)
    all_frames: List[pd.DataFrame] = []

    for scenario_dir in sorted(data_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue
        conn_log = scenario_dir / "conn.log"
        label_file = scenario_dir / "conn.log.labeled"

        if not conn_log.exists():
            continue

        flows = parse_zeek_conn_log(conn_log)
        if flows.empty:
            continue

        if label_file.exists():
            label_lines = label_file.read_text(errors="replace").splitlines()
            flows = align_labels(flows, label_lines)
        else:
            flows["label"] = "Unknown"

        flows["dataset"] = "iot23"
        all_frames.append(flows)

    if not all_frames:
        raise FileNotFoundError(f"No IoT-23 scenario directories found in {data_dir}")

    combined = pd.concat(all_frames, ignore_index=True)
    combined = combined.dropna(subset=["src_ip", "dst_ip", "label"])
    combined = combined[combined["label"] != "Unknown"].reset_index(drop=True)

    # Use stratified split when every class has >= 2 members; fall back otherwise
    # (e.g. tiny test fixtures or rare-label scenarios with a single sample).
    min_class_count = combined["label"].value_counts().min()
    stratify = combined["label"] if min_class_count >= 2 else None

    train_df, test_df = train_test_split(
        combined,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
    return {
        "train": train_df.reset_index(drop=True),
        "test": test_df.reset_index(drop=True),
    }
