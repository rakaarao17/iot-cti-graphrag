# ADR-002: Centralized Exception Hierarchy with Structured Error Envelope

Status: Accepted
Date: 2026-06-11
North Star: Ensure errors are honest, actionable, and traceable throughout the system

## Context

The original codebase had ad-hoc error handling:
- Different modules raised different exception types (or returned error strings)
- No consistent structure for error details, recovery hints, or error codes
- Difficult for evaluators to debug failures without diving into code
- LLM hallucination detection wasn't integrated with error reporting

For academic reproducibility, errors must be **explicit, structured, and debuggable**.

## Decision

Create a centralized exception hierarchy under `src/core/exceptions.py`:

```python
AppError (base)
├── ValidationError (config validation, input validation)
│   └── ConfigError (specifically config-related)
├── GraphError (Neo4j failures)
├── LLMError (Ollama, Gemini failures)
├── EmbeddingError (embedding service failures)
├── DataError (data processing, format errors)
├── NotFoundError (resource not found)
├── HallucinationDetectedError (LLM output validation failures)
└── TimeoutError (operation timeouts)
```

Each exception has:
- **code** — machine-readable error identifier (e.g., "GRAPH_ERROR")
- **http_status** — REST status code (for future HTTP wrapper)
- **message** — human-readable summary
- **details** — structured context (dict)
- **recovery_hint** — actionable recovery suggestion

Example:
```python
raise ConfigError(
    message="NEO4J_URI environment variable not set",
    code="CONFIG_ERROR",
    details={"variable": "NEO4J_URI"},
    recovery_hint="Check .env file and ensure NEO4J_URI is set. See .env.example for reference.",
)
```

All exceptions serialize to structured JSON:
```json
{
  "error": {
    "code": "CONFIG_ERROR",
    "message": "Configuration error",
    "details": {"variable": "NEO4J_URI"},
    "recovery_hint": "Check .env file and ensure NEO4J_URI is set..."
  }
}
```

## Alternatives

A) **No centralization** — Keep ad-hoc exception types.
   - Rejected: Inconsistent error handling; hard to debug.

B) **Use a library** (e.g., HTTPException, Pydantic ValidationError)
   - Rejected: External dependencies add complexity; in-house solution is simpler.

C) **Simple flat exception types** — No hierarchy.
   - Rejected: Doesn't capture relationships (e.g., ConfigError is a ValidationError).

## Consequences

### Positive
- ✅ Structured error envelope: All errors have the same shape
- ✅ Clear error codes: Easy to search logs and trace issues
- ✅ Actionable recovery: Each error includes a hint for resolution
- ✅ Hierarchy: Better error handling (catch ValidationError catches ConfigError)
- ✅ Serializable: Errors can be logged as JSON or returned via API

### Negative
- ⚠️ Boilerplate: Every place that raises an exception needs to be explicit
- ⚠️ Learning curve: Teams must learn the exception hierarchy

### Mitigation
- **Boilerplate**: Minimal; exceptions are rare and important
- **Learning**: Exception hierarchy is simple and well-documented

## Related Decisions

- ADR-001: Hexagonal Architecture (adapters raise structured exceptions)
