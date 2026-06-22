# ADR-001: Hexagonal (Ports & Adapters) Architecture

Status: Accepted
Date: 2026-06-11
North Star: Build a factual, explainable AI system for IoT threat analysis with offline operation and swappable LLM backends

## Context

The original codebase had tight coupling to specific services:
- LLM locked to Ollama via direct imports and hardcoded connection strings
- Graph operations tightly coupled to Neo4j query syntax
- No interface abstractions, making testing and service swapping difficult
- Error handling inconsistent across modules; no structured error envelope

For a dissertation project with peer review, this creates risks:
- Difficult to test without fully configured external services
- Evaluators cannot easily substitute different LLMs (OpenAI, local Gemma, etc.)
- Refactoring or maintenance becomes risky due to hidden dependencies

## Decision

Adopt **Hexagonal (Ports & Adapters) architecture** to create:

1. **Ports** — Abstract interfaces (LLMPort, GraphPort, EmbeddingPort)
2. **Adapters** — Concrete implementations (OllamaAdapter, Neo4jAdapter)
3. **Core** — Domain logic independent of I/O (exceptions, config, services)
4. **Tests** — Mock adapters enabling unit tests without external services

Structure:
```
src/
  core/               # Domain logic, exceptions, config
  ports/              # Abstractions (LLMPort, GraphPort, etc.)
  adapters/           # Implementations (Ollama, Neo4j, mocks)
  stage1_*/           # 6-stage pipeline (unchanged interface, internal only)
```

## Alternatives

A) **No refactoring** — Keep original structure.
   - Rejected: Risks research credibility; hard to test; hard to extend.

B) **Full rewrite to MVC** — Restructure as web framework (Django, Flask).
   - Rejected: Overkill for a research tool; not a web app; adds bloat.

C) **Minimal cleanup** — Just remove dead code, no architecture change.
   - Rejected: Doesn't address the core coupling problem; testing still hard.

## Consequences

### Positive
- ✅ Swappable LLMs: Evaluator can substitute any LLM implementing LLMPort
- ✅ Testable: Mock adapters enable unit tests without Neo4j or Ollama
- ✅ Clear separation of concerns: Domain logic independent of I/O
- ✅ Structured errors: All exceptions inherit from AppError with consistent envelope
- ✅ Validated config at boot: Required environment variables checked before pipeline runs
- ✅ Research credibility: Explicit dependencies, clear interfaces, mockable services

### Negative
- ⚠️ Complexity: More files, more abstractions to understand
- ⚠️ Boilerplate: Each adapter must fully implement its port
- ⚠️ Migration effort: Existing stages need minimal updates to use adapters

### Mitigation
- **Complexity**: Comprehensive ADR documentation and smoke tests mitigate learning curve
- **Boilerplate**: Standard templates for adapter implementations
- **Migration**: Backward-compatible; old code paths work, new code uses adapters

## Related Decisions

- ADR-002: Centralized Exception Handling
- ADR-003: Config Validation at Boot
- ADR-004: Smoke Test Strategy
