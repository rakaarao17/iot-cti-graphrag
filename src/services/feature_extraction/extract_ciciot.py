"""CICIoT2023 feature extraction with train/test split.

Supports two CSV formats:
  - Raw flow format: columns include src_ip, dst_ip, flow_id, label, etc.
  - Pre-extracted format: 39 numeric feature columns (Header_Length, Protocol Type,
    Time_To_Live, ...). Label is derived from the filename stem.
"""

import uuid
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.model_selection import train_test_split

REQUIRED_COLUMNS = [
    "uid", "src_ip", "dst_ip", "src_port", "dst_port",
    "protocol", "duration", "fwd_pkts", "bwd_pkts",
    "fwd_bytes", "bwd_bytes", "label", "dataset",
]

# Columns present in the pre-extracted format that signal it is NOT raw-flow data.
_PRE_EXTRACTED_SIGNALS = {"header_length", "protocol_type", "time_to_live", "rate"}

# Raw-flow column name -> our normalized name
_RAW_FLOW_COLUMN_MAP = {
    "flow_id":           "uid",
    "src_ip":            "src_ip",
    "dst_ip":            "dst_ip",
    "src_port":          "src_port",
    "dst_port":          "dst_port",
    "protocol":          "protocol",
    "flow_duration":     "duration",
    "tot_fwd_pkts":      "fwd_pkts",
    "tot_bwd_pkts":      "bwd_pkts",
    "totlen_fwd_pkts":   "fwd_bytes",
    "totlen_bwd_pkts":   "bwd_bytes",
    "label":             "label",
}


def extract_ciciot(
    data_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Load CICIoT2023 CSV files, normalize schema, split into train/test.

    Handles both raw-flow CSVs (with src_ip/dst_ip/label columns) and
    pre-extracted feature CSVs (39 numeric columns; label from filename).

    Returns:
        {"train": DataFrame, "test": DataFrame} with at minimum REQUIRED_COLUMNS
        plus any extra feature columns present in the source CSVs.
    """
    data_dir = Path(data_dir)
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    frames = []
    for f in csv_files:
        df = pd.read_csv(f, low_memory=False)
        normalized_cols = {c.lower().strip().replace(" ", "_") for c in df.columns}

        if _PRE_EXTRACTED_SIGNALS & normalized_cols:
            frames.append(_normalize_pre_extracted(df, f.stem))
        else:
            frames.append(_normalize_raw_flow(df))

    raw = pd.concat(frames, ignore_index=True)
    raw = raw.dropna(subset=["label"])
    raw = raw.reset_index(drop=True)

    raw = raw[raw["label"].astype(str).str.strip() != ""]

    train_df, test_df = train_test_split(
        raw,
        test_size=test_size,
        random_state=random_state,
        stratify=raw["label"],
    )
    return {
        "train": train_df.reset_index(drop=True),
        "test": test_df.reset_index(drop=True),
    }


def _label_from_stem(stem: str) -> str:
    """Derive attack label from CSV filename stem.

    Examples:
        BenignTraffic.pcap  -> Benign
        DDoS-TCP_Flood.pcap -> DDoS-TCP_Flood
        SqlInjection.pcap   -> SqlInjection
    """
    name = stem.replace(".pcap", "")
    if name == "BenignTraffic":
        return "Benign"
    return name


def _normalize_pre_extracted(df: pd.DataFrame, stem: str) -> pd.DataFrame:
    """Normalize a pre-extracted 39-feature CICIoT CSV."""
    df = df.copy()
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]

    label = _label_from_stem(stem)
    df["label"] = label

    # IPs are not available in this format -- use sentinel so downstream
    # code that requires the column still works.
    df["src_ip"] = "0.0.0.0"
    df["dst_ip"] = "0.0.0.0"
    df["src_port"] = 0
    df["dst_port"] = 0

    # Map pre-extracted columns to normalized flow-feature names.
    # The originals are kept so XGBoost can use the richer feature set.
    df["duration"] = pd.to_numeric(df.get("iat", 0), errors="coerce").fillna(0.0)
    df["fwd_pkts"] = pd.to_numeric(df.get("number", 0), errors="coerce").fillna(0.0)
    df["bwd_pkts"] = 0.0
    df["fwd_bytes"] = pd.to_numeric(df.get("tot_size", 0), errors="coerce").fillna(0.0)
    df["bwd_bytes"] = 0.0
    df["protocol"] = df["protocol_type"].astype(str) if "protocol_type" in df.columns else "unknown"

    df["uid"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["dataset"] = "ciciot2023"

    return df


def _normalize_raw_flow(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a raw-flow CICIoT CSV (original format with src_ip/dst_ip)."""
    df = df.copy()
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={k: v for k, v in _RAW_FLOW_COLUMN_MAP.items() if k in df.columns})

    if "uid" not in df.columns:
        df["uid"] = [str(uuid.uuid4()) for _ in range(len(df))]
    else:
        df["uid"] = df["uid"].astype(str)

    df["dataset"] = "ciciot2023"

    for col in ["src_port", "dst_port"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["fwd_pkts", "bwd_pkts", "fwd_bytes", "bwd_bytes"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "duration" in df.columns:
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0.0)
    if "protocol" in df.columns:
        df["protocol"] = df["protocol"].astype(str)

    keep = [c for c in REQUIRED_COLUMNS if c in df.columns]
    return df[keep]
