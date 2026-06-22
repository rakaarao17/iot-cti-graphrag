"""
Stage 2: Unified Feature Engineering.

Combines IoT-23 and CICIoT2023 processed data into a single dataset
with derived features for knowledge graph construction.
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DATA_PROCESSED_DIR, logger
from config.schema import WELL_KNOWN_PORTS, UNIFIED_FEATURE_COLUMNS


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features to the unified dataset."""
    df = df.copy()

    # -- Bytes ratio --
    total_bytes = (df["orig_bytes"].fillna(0) + df["resp_bytes"].fillna(0)).replace(0, 1)
    df["bytes_ratio"] = (df["orig_bytes"].fillna(0) / total_bytes).round(4)

    # -- Packet ratio --
    total_pkts = (df["orig_pkts"].fillna(0) + df["resp_pkts"].fillna(0)).replace(0, 1)
    df["packet_ratio"] = (df["orig_pkts"].fillna(0) / total_pkts).round(4)

    # -- Bytes per packet --
    df["bytes_per_pkt"] = (total_bytes / total_pkts).round(2)

    # -- Duration category --
    def categorize_duration(dur):
        if pd.isna(dur) or dur <= 0:
            return "instant"
        elif dur < 1:
            return "short"
        elif dur < 60:
            return "medium"
        else:
            return "long"

    df["duration_cat"] = df["duration"].apply(categorize_duration)

    # -- Port category --
    def categorize_port(port):
        if pd.isna(port):
            return "unknown"
        port = int(port)
        if port in WELL_KNOWN_PORTS:
            return "well-known"
        elif port < 1024:
            return "system"
        elif port < 49152:
            return "registered"
        else:
            return "dynamic"

    df["port_category"] = df["dst_port"].apply(categorize_port)

    return df


def combine_datasets(
    iot23_file: Path = None,
    ciciot_file: Path = None,
    output_file: Path = None,
) -> pd.DataFrame:
    """
    Combine IoT-23 and CICIoT2023 processed datasets into unified format.

    Returns the combined DataFrame with all derived features.
    """
    iot23_file = iot23_file or (DATA_PROCESSED_DIR / "iot23_features.csv")
    ciciot_file = ciciot_file or (DATA_PROCESSED_DIR / "ciciot_features.csv")
    output_file = output_file or (DATA_PROCESSED_DIR / "unified_features.csv")

    dfs = []

    # Load IoT-23
    if iot23_file.exists():
        df_iot23 = pd.read_csv(iot23_file, low_memory=False)
        logger.info(f"Loaded IoT-23: {len(df_iot23):,} rows")
        dfs.append(df_iot23)
    else:
        logger.warning(f"IoT-23 processed file not found: {iot23_file}")

    # Load CICIoT2023
    if ciciot_file.exists():
        df_ciciot = pd.read_csv(ciciot_file, low_memory=False)
        logger.info(f"Loaded CICIoT2023: {len(df_ciciot):,} rows")
        dfs.append(df_ciciot)
    else:
        logger.warning(f"CICIoT2023 processed file not found: {ciciot_file}")

    if not dfs:
        logger.error("No processed data files found. Run extraction first.")
        return pd.DataFrame()

    # Combine
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataset: {len(combined):,} rows")

    # Ensure consistent column types
    for col in ["orig_bytes", "resp_bytes", "orig_pkts", "resp_pkts", "src_port", "dst_port"]:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col], errors="coerce").fillna(0)

    combined["duration"] = pd.to_numeric(combined["duration"], errors="coerce").fillna(0)

    # Add derived features
    combined = add_derived_features(combined)
    logger.info(f"Added derived features. Final columns: {len(combined.columns)}")

    # Fill missing values
    combined["service"] = combined["service"].fillna("unknown")
    combined["conn_state"] = combined["conn_state"].fillna("OTH")
    combined["protocol"] = combined["protocol"].fillna("TCP")
    combined["attack_category"] = combined["attack_category"].fillna("Unknown")

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_file, index=False)
    logger.info(f"Saved unified features: {output_file}")

    # Summary statistics
    print("\n" + "=" * 70)
    print("  UNIFIED DATASET SUMMARY")
    print("=" * 70)
    print(f"  Total Flows:    {len(combined):,}")
    print(f"  Total Columns:  {len(combined.columns)}")
    print(f"  Unique Src IPs: {combined['src_ip'].nunique():,}")
    print(f"  Unique Dst IPs: {combined['dst_ip'].nunique():,}")
    print(f"  Protocols:      {combined['protocol'].unique().tolist()}")
    print(f"\n  Attack Category Distribution:")
    for cat, count in combined["attack_category"].value_counts().items():
        bar = "#" * int(count / len(combined) * 50)
        print(f"    {cat:25s} {count:8,d} ({count/len(combined)*100:5.1f}%) {bar}")
    print(f"\n  Dataset Distribution:")
    for ds, count in combined["dataset"].value_counts().items():
        print(f"    {ds:25s} {count:8,d} ({count/len(combined)*100:5.1f}%)")
    print("=" * 70)

    return combined


if __name__ == "__main__":
    df = combine_datasets()
    if not df.empty:
        print(f"\nFinal dataset shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
