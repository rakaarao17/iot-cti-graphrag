# ADR-0007: Unify Configuration Sources (config/ and src/core/config.py)

Status:     Implemented (2026-06-25; supersedes the original "defer" decision of 2026-06-23)
Date:       2026-06-23 (deferred) -> 2026-06-25 (implemented post-submission)
North Star: A single, validated source of truth for configuration, achieved without
            changing any value the evaluation pipeline was run with.

## Update (2026-06-25) -- Implemented
`src/core/config.py` (`Config` / `get_config()`) is now the **single canonical source**.
`config/settings.py` derives every shared value from `get_config()` and retains only
pipeline-only constants (node2vec params, dataset URLs, sampling, `logger`). All ~30
existing `from config.settings import X` call sites are unchanged.

**Zero result drift, enforced by a test.** The pipeline previously ran with literal
`LLM_TEMPERATURE=0.3` and `LLM_MAX_TOKENS=4096` in `settings.py`, while `Config` defaulted
to `0.7`/`2048` (and `.env.example` documented the latter). The proven pipeline values
(temp 0.3, max_tokens 4096, model `gemma4:e2b`, 384-dim local embeddings) are now the
canonical defaults and are pinned in `.env.example`. `tests/unit/test_config_unified.py`
asserts (a) settings == Config for all shared keys and (b) the proven values are preserved,
so any future drift fails CI. Verified: full suite 8/8.

## Context
The codebase reads runtime configuration from two distinct sources:

- The root `config/` package (`config.settings`, `config.schema`) is imported by all
  pipeline services (`src/services/**`) and the pipeline scripts (`scripts/**`).
- `src/core/config.py` is imported by the hexagonal layer — `src/adapters/**` and the
  test suite.

This split is a side effect of layering the Ports & Adapters structure (ADR-0001,
ADR-0005) on top of the original script-based pipeline. Both configs currently work;
there is no runtime conflict, only duplication of where settings live.

## Original Decision (2026-06-23, now superseded)
Leave both configuration sources in place near submission and document the seam, rather
than risk a wide refactor. This was the right call pre-submission; post-submission it was
implemented as described in the Update above.

## Alternatives
- Unify everything into `src/core/config.py` now — rejected: ~30 files import the root
  `config/` package; rewriting them days before the thesis deadline carries high
  regression risk for marginal benefit on a working system.
- Defer silently — rejected: an undocumented dual-config is exactly the kind of
  hidden seam that erodes reviewer trust. Documenting it is the honest middle path.

## Consequences
- Positive: Zero risk to the working pipeline; the dual-config is now explicit and
  discoverable (README + this ADR) instead of a surprise during code review.
- Negative: New contributors must know which layer reads which config; some settings
  are defined in both places.
- Mitigation: README "Config note" points here. Unifying into a single config source
  is recorded as future work in docs/ROADMAP.md / KNOWN_LIMITATIONS.md.
