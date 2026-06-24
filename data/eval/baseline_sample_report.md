# XGBoost Baseline - CICIoT2023 SAMPLE

> **Sample-based.** Trained on `data/samples/ciciot2023_sample.csv` (24,996 rows). This is NOT the full-dataset 39-feature baseline, which requires the raw CICIoT2023 data in `data/raw/ciciot2023` (not present in this checkout).

## Metrics

- **Macro F1:** 0.2451
- **AUC-ROC (OVR macro):** 0.8725
- **Train / Test:** 19,996 / 5,000
- **Classes:** 34
- **Features (10):** duration, src_port, dst_port, orig_bytes, resp_bytes, orig_pkts, resp_pkts, bytes_ratio, packet_ratio, bytes_per_pkt

## Top feature importances

| Feature | Importance |
|---|---|
| orig_pkts | 0.7995 |
| orig_bytes | 0.0704 |
| bytes_per_pkt | 0.0673 |
| resp_bytes | 0.0406 |
| bytes_ratio | 0.0105 |
| resp_pkts | 0.0066 |
| packet_ratio | 0.0050 |
| duration | 0.0000 |
