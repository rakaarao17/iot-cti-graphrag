# ADR-0006: Phantom Code Documentation Strategy

Status:     Accepted
Date:       2026-06-16
North Star: Maintains transparency and trust in the pipeline while allowing for seamless portfolio demonstrations.

## Context
During the code audit, we identified two "phantoms" (stub integrations):
1. **Dataset Downloaders**: Automated downloading of the CICIoT2023 and IoT-23 datasets is either entirely manual instructions or falls back to synthetic data generation.
2. **Text Embeddings**: If `GOOGLE_API_KEY` is missing, the code silently falls back to `np.random.randn()` arrays, allowing the pipeline to finish but destroying semantic search accuracy.

## Decision
Instead of realizing the features (e.g., adding complex S3/Kaggle API integrations) or removing them (which would break the `run_evaluator.bat` flow), we chose to **DECLARE** them. We added explicit `⚠️ DEMO STUB — NOT PRODUCTION READY` headers to the respective files.

## Alternatives
- Realize — rejected: Requires third-party credentials and significantly increases the complexity of a demonstration.
- Remove — rejected: Removing the synthetic fallback would make it impossible to run the pipeline without a valid Google API key, hindering local testing.

## Consequences
- Positive: Evaluators can run the code from start to finish without needing API keys or gigabytes of bandwidth.
- Negative: The semantic search capability will return hallucinated context if an API key is not provided.
- Mitigation: The README and source files explicitly warn about these limitations.
