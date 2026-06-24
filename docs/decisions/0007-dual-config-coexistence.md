# ADR-0007: Accept Dual Configuration Sources (config/ and src/core/config.py)

Status:     Accepted
Date:       2026-06-23
North Star: Keep the working thesis pipeline stable while documenting a known
            architectural seam honestly, rather than risking a wide refactor near submission.

## Context
The codebase reads runtime configuration from two distinct sources:

- The root `config/` package (`config.settings`, `config.schema`) is imported by all
  pipeline services (`src/services/**`) and the pipeline scripts (`scripts/**`).
- `src/core/config.py` is imported by the hexagonal layer — `src/adapters/**` and the
  test suite.

This split is a side effect of layering the Ports & Adapters structure (ADR-0001,
ADR-0005) on top of the original script-based pipeline. Both configs currently work;
there is no runtime conflict, only duplication of where settings live.

## Decision
Leave both configuration sources in place for now and document the seam. We do **not**
unify them at this time.

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
