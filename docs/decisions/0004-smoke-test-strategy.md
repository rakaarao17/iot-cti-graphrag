# ADR-004: Smoke Test Strategy for Research Credibility

Status: Accepted
Date: 2026-06-11
North Star: Provide automated validation that the system is deployable and functional

## Context

The original codebase had end-to-end tests (in `scripts/run_automated_tests.py`) but:
- Took 30+ minutes to run (full graph ingestion)
- Required all external services (Neo4j, Ollama, Gemini)
- Only ran after everything was already built
- Couldn't validate code changes quickly

For academic work, we need:
1. **Instant feedback** on code changes (< 30 sec)
2. **No external dependencies** for basic validation
3. **Clear pass/fail** indicators
4. **Reproducible** on evaluator's machine

## Decision

Create `tests/smoke/test_core.py` with five minimal smoke tests:

1. **Import Integrity** — Dynamically imports all source modules
   - Catches circular dependencies, missing imports, syntax errors
   - Result: All 8 core modules importable
   
2. **Exception Hierarchy** — Verify exceptions are structured correctly
   - Test exception creation, serialization, recovery hints
   - Result: All exceptions have `.to_dict()` and `.to_json()` methods
   
3. **Port Abstraction** — Verify ports cannot be instantiated directly
   - Test that LLMPort, GraphPort are abstract
   - Result: TypeError when trying to instantiate
   
4. **Adapter Contracts** — Verify adapters implement their ports
   - Test MockLLMAdapter implements LLMPort
   - Test MockGraphAdapter implements GraphPort
   - Result: isinstance() checks pass
   
5. **Mock Adapters Functional** — Verify mock adapters work standalone
   - Test MockLLMAdapter.generate() returns strings
   - Test MockGraphAdapter.run_query() returns results
   - Result: All methods work without external services

**Run command:**
```bash
python tests/smoke/test_core.py
```

**Output:**
```
Results: 5 passed, 0 failed
```

## Alternatives

A) **No automated tests** — Just manual testing.
   - Rejected: Not reproducible; hard for evaluators to validate.

B) **Full integration tests** — Test entire pipeline.
   - Rejected: Takes 30+ minutes; requires all services; fails too late.

C) **PyTest framework** — Use industry-standard testing.
   - Rejected: Added dependency; simple runner is sufficient.

## Consequences

### Positive
- ✅ Fast feedback: Runs in < 5 seconds
- ✅ No dependencies: Works without Neo4j, Ollama, Gemini
- ✅ Clear validation: Pass/fail immediately visible
- ✅ Reproducible: Evaluator can run anytime, anywhere
- ✅ Research credibility: Automated validation shows confidence

### Negative
- ⚠️ Limited scope: Doesn't test end-to-end pipeline
- ⚠️ Mock data: Tests use deterministic mock responses

### Mitigation
- **Limited scope**: Smoke tests complement end-to-end tests in `scripts/`
- **Mock data**: Mock adapters have realistic response shapes

## Related Decisions

- ADR-001: Hexagonal Architecture (enables mock adapters for testing)
- ADR-002: Exception Hierarchy (smoke tests verify exceptions are structured)
