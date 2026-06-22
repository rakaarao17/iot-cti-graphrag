# ADR-0005: Restructure Pipeline Stages to Services

Status:     Accepted
Date:       2026-06-16
North Star: Enables a truly modular GraphRAG architecture rather than a rigid script-based pipeline.

## Context
The application was originally structured sequentially as `stage1_data_acquisition`, `stage2_feature_extraction`, up to `stage6`. While this reflects the initial data flow, it violates the intended Hexagonal Architecture by treating core domain services as temporary scripts. The CLI was also coupled tightly within `stage6`.

## Decision
We moved all domain logic from `stageX_*` folders into a unified `src/services/` directory and extracted the interactive terminal logic into `src/cli/main.py`.

## Alternatives
- Leave as sequential stages — rejected: Difficult to scale, hard to run isolated services without orchestrator assumptions.
- Full Hexagonal (Strict Core/Ports/Adapters) — rejected: Too heavyweight for a portfolio/demo project, we opted for a balanced approach with `services`, `ports`, and `adapters`.

## Consequences
- Positive: Clearer separation of concerns. The CLI is now an independent consumer of the `ThreatExplainer` service.
- Negative: Required updating all import paths across the codebase.
- Mitigation: Ran comprehensive smoke tests (`test_core.py`) to verify import integrity.
