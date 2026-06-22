# LLM Model Comparison Report

**Generated:** 2026-06-22T10:42:19.589611+00:00
**Total queries:** 20

## Per-Model Summary

| Model | Deployment | Mean Latency (ms) | Median Latency (ms) | Mean Grounding | Mean Tokens | Error Rate |
|-------|------------|-------------------|---------------------|----------------|-------------|------------|
| gemma4:e2b | local | 34906.2 | 33343.4 | 0.600 | 39 | 0.100 |
| phi3:latest | local | 14793.1 | 14086.8 | 0.851 | 299 | 0.000 |
| zeroday-phi3-ciciot-v2:latest | local | 11241.6 | 10322.2 | 0.949 | 139 | 0.000 |

## Per-Query Grounding Ratios

| Query ID | Category | gemma4:e2b | phi3:latest | zeroday-phi3-ciciot-v2:latest |
|----------|----------|----------|----------|----------|
| te-01 | threat_explanation | 0.000 | 0.857 | 0.833 |
| te-02 | threat_explanation | 0.000 | 0.750 | 1.000 |
| te-03 | threat_explanation | 0.000 | 0.667 | 0.800 |
| te-04 | threat_explanation | 1.000 | 0.833 | 0.800 |
| is-01 | incident_summary | 1.000 | 1.000 | 1.000 |
| is-02 | incident_summary | 1.000 | 1.000 | 1.000 |
| is-03 | incident_summary | 1.000 | 0.800 | 1.000 |
| is-04 | incident_summary | 1.000 | 0.857 | 1.000 |
| ac-01 | attack_classification | 1.000 | 0.938 | 1.000 |
| ac-02 | attack_classification | 0.000 | 0.778 | 1.000 |
| ac-03 | attack_classification | 0.000 | 0.857 | 1.000 |
| ac-04 | attack_classification | 1.000 | 1.000 | 1.000 |
| aq-01 | analyst_qa | 0.000 | 1.000 | 1.000 |
| aq-02 | analyst_qa | 1.000 | 0.778 | 1.000 |
| aq-03 | analyst_qa | 0.000 | 0.800 | 1.000 |
| aq-04 | analyst_qa | 0.000 | 0.750 | 1.000 |
| es-01 | executive_summary | 1.000 | 0.714 | 0.750 |
| es-02 | executive_summary | 1.000 | 0.750 | 0.800 |
| es-03 | executive_summary | 1.000 | 0.889 | 1.000 |
| es-04 | executive_summary | 1.000 | 1.000 | 1.000 |
