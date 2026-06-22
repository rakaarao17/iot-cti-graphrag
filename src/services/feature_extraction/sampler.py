"""
Stage 2: Stratified Sampler.

Creates representative subsets of the unified dataset preserving
attack-type distribution for faster development and testing.
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DATA_PROCESSED_DIR, DATA_SAMPLES_DIR, DEFAULT_SAMPLE_SIZE, logger


def stratified_sample(
    df: pd.DataFrame,
    n_samples: int = None,
    stratify_col: str = "attack_category",
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Create a stratified sample preserving the distribution of attack types.

    If any category has fewer samples than needed for its proportion,
    all samples from that category are included (oversampling avoided).
    """
    n_samples = n_samples or DEFAULT_SAMPLE_SIZE

    if len(df) <= n_samples:
        logger.info(f"Dataset ({len(df):,}) smaller than sample size ({n_samples:,}). Using full dataset.")
        return df.copy()

    # Calculate desired counts per category
    category_counts = df[stratify_col].value_counts()
    category_proportions = category_counts / len(df)
    desired_counts = (category_proportions * n_samples).astype(int)

    # Ensure at least 1 sample per category
    desired_counts = desired_counts.clip(lower=1)

    # Adjust if total exceeds n_samples
    while desired_counts.sum() > n_samples:
        max_cat = desired_counts.idxmax()
        desired_counts[max_cat] -= 1

    # Sample from each category
    sampled_dfs = []
    for category, desired_n in desired_counts.items():
        cat_df = df[df[stratify_col] == category]
        actual_n = min(desired_n, len(cat_df))
        sampled = cat_df.sample(n=actual_n, random_state=random_state)
        sampled_dfs.append(sampled)

    result = pd.concat(sampled_dfs, ignore_index=True)

    # Shuffle the final result
    result = result.sample(frac=1, random_state=random_state).reset_index(drop=True)

    logger.info(f"Stratified sample: {len(result):,} rows from {len(df):,}")
    logger.info(f"Categories preserved: {result[stratify_col].nunique()}")

    return result


def create_dev_samples(
    unified_file: Path = None,
    sample_size: int = None,
):
    """
    Create development sample files from the unified dataset.

    Generates:
    - samples/dev_sample.csv -- main development sample
    - samples/iot23_sample.csv -- IoT-23 only sample
    - samples/ciciot_sample.csv -- CICIoT2023 only sample
    """
    unified_file = unified_file or (DATA_PROCESSED_DIR / "unified_features.csv")
    sample_size = sample_size or DEFAULT_SAMPLE_SIZE

    if not unified_file.exists():
        logger.error(f"Unified features file not found: {unified_file}")
        return

    df = pd.read_csv(unified_file, low_memory=False)
    logger.info(f"Loaded unified dataset: {len(df):,} rows")

    DATA_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    # Full stratified sample
    dev_sample = stratified_sample(df, n_samples=sample_size)
    dev_file = DATA_SAMPLES_DIR / "dev_sample.csv"
    dev_sample.to_csv(dev_file, index=False)
    logger.info(f"Saved dev sample: {dev_file} ({len(dev_sample):,} rows)")

    # Per-dataset samples
    for dataset_name in df["dataset"].unique():
        ds_df = df[df["dataset"] == dataset_name]
        ds_sample = stratified_sample(ds_df, n_samples=sample_size // 2)
        ds_file = DATA_SAMPLES_DIR / f"{dataset_name.lower().replace(' ', '_')}_sample.csv"
        ds_sample.to_csv(ds_file, index=False)
        logger.info(f"Saved {dataset_name} sample: {ds_file} ({len(ds_sample):,} rows)")

    # Print distribution comparison
    print("\n" + "=" * 70)
    print("  SAMPLE DISTRIBUTION COMPARISON")
    print("=" * 70)

    orig_dist = df["attack_category"].value_counts(normalize=True)
    sample_dist = dev_sample["attack_category"].value_counts(normalize=True)

    print(f"  {'Category':25s} {'Original':>10s} {'Sample':>10s} {'Diff':>8s}")
    print(f"  {'-' * 55}")
    for cat in orig_dist.index:
        orig_pct = orig_dist.get(cat, 0) * 100
        samp_pct = sample_dist.get(cat, 0) * 100
        diff = samp_pct - orig_pct
        print(f"  {cat:25s} {orig_pct:9.1f}% {samp_pct:9.1f}% {diff:+7.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create stratified data samples")
    parser.add_argument("--size", type=int, default=DEFAULT_SAMPLE_SIZE, help="Sample size")
    args = parser.parse_args()

    create_dev_samples(sample_size=args.size)
