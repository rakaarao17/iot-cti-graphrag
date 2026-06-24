# XGBoost Baseline - UNIFIED (CICIoT + IoT-23)

> Trained on a stratified sample of `data/processed/unified_features.csv` (1,500,000 of 5.5M rows) using the Zeek-flow feature schema the knowledge graph is built from -- the fairest head-to-head vs GraphRAG. IoT-23 rows are all `Benign`. **Distinct** from `baseline_full_report` (CICIoT 46 pre-extracted features).

> **Why a sample:** a single-shot XGBoost fit on all 5.5M rows collapses to a degenerate near-random model (F1~0.05, AUC~0.51). A size sweep (200k -> 0.255/0.903, 1M -> 0.262/0.907) shows the learning curve has converged, so a 1.5M stratified sample is the representative baseline.

## Metrics

- **Macro F1:** 0.2578
- **AUC-ROC (OVR macro):** 0.907
- **Train / Test:** 1,200,000 / 300,000
- **Classes:** 34
- **Features (10):** duration, src_port, dst_port, orig_bytes, resp_bytes, orig_pkts, resp_pkts, bytes_ratio, packet_ratio, bytes_per_pkt

## Top feature importances

| Feature | Importance |
|---|---|
| src_port | 0.8840 |
| orig_pkts | 0.0578 |
| resp_pkts | 0.0286 |
| resp_bytes | 0.0125 |
| bytes_per_pkt | 0.0087 |
| orig_bytes | 0.0075 |
| bytes_ratio | 0.0005 |
| duration | 0.0004 |
| dst_port | 0.0001 |
| packet_ratio | 0.0001 |
