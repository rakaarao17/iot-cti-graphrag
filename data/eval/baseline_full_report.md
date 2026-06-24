# XGBoost Baseline - FULL Dataset

Datasets: **ciciot** (raw, no sampling). No ablation re-run.

## Metrics

- **Macro F1:** 0.6558
- **AUC-ROC (OVR macro):** 0.9844
- **Train / Test:** 3,474,573 / 868,644
- **Classes:** 34
- **Features used:** 46

## Top feature importances

| Feature | Importance |
|---|---|
| protocol_type | 0.2278 |
| syn_count | 0.1729 |
| icmp | 0.0889 |
| fin_flag_number | 0.0713 |
| udp | 0.0688 |
| fwd_pkts | 0.0565 |
| psh_flag_number | 0.0337 |
| ack_flag_number | 0.0321 |
| fin_count | 0.0299 |
| rst_flag_number | 0.0294 |
