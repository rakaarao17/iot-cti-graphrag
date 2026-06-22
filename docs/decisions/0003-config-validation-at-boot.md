# ADR-003: Config Validation at Boot

Status: Accepted
Date: 2026-06-11
North Star: Fail fast and clearly if the system is misconfigured

## Context

The original codebase loaded config lazily:
- Environment variables accessed via `os.getenv()` calls scattered throughout code
- Failures only discovered when a particular code path was reached
- Difficult to validate a complete configuration before running long-running tasks
- Neo4j password hardcoded as "password" without validation

For academic work, the evaluator must know immediately if something is misconfigured:
- Running a 60-minute graph ingestion pipeline only to fail at the end is unacceptable
- Required variables should be validated before any significant work begins

## Decision

Create `src/core/config.py` with a `Config` class that:

1. **Loads at boot**: `init_config()` called early in program startup
2. **Validates all required fields**: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, etc.
3. **Provides defaults** for optional fields: LOG_LEVEL defaults to "INFO", etc.
4. **Raises ConfigError immediately** if any required field is missing
5. **Creates directories** if they don't exist (e.g., data/raw, data/processed)
6. **Single source of truth**: All code uses `get_config()` instead of `os.getenv()`

Example:
```python
from src.core.config import init_config

# At program startup (before any pipeline work):
config = init_config()  # Validates and raises ConfigError if invalid

# Later, anywhere in code:
from src.core.config import get_config
config = get_config()
neo4j_uri = config.NEO4J_URI  # Type-safe, guaranteed to be set
```

## Alternatives

A) **Lazy config loading** — Keep current `os.getenv()` approach.
   - Rejected: Failures too late; hard to debug.

B) **External config library** (e.g., Pydantic, python-decouple)
   - Rejected: Adds external dependency; in-house solution is simpler.

C) **Multiple config files** (development, production, test)
   - Rejected: Unnecessary complexity for research tool; single .env is sufficient.

## Consequences

### Positive
- ✅ Fail fast: Configuration errors caught at program start
- ✅ Clear error messages: ConfigError includes hints for fixing the problem
- ✅ Type-safe: `config.NEO4J_URI` vs `os.getenv("NEO4J_URI")`
- ✅ Single source of truth: All config centralized
- ✅ Testable: Can mock config for unit tests

### Negative
- ⚠️ Initialization overhead: Small startup cost to validate config
- ⚠️ Less flexibility: Can't change config at runtime (not needed for this project)

### Mitigation
- **Initialization overhead**: Negligible (< 1 sec)
- **Flexibility**: Not needed for research tool; config is per-run

## Related Decisions

- ADR-002: Exception Hierarchy (ConfigError raised here)
- ADR-001: Hexagonal Architecture (adapters use validated config)
