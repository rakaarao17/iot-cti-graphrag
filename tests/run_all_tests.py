"""
Test Runner for Phase 3: Full Integration Testing

Runs all smoke tests, unit tests, and integration tests
to validate the entire system.
"""

import os
import sys
from pathlib import Path
import subprocess

project_root = Path(__file__).resolve().parent.parent

# Child test files print Unicode status glyphs; force UTF-8 in the subprocess
# so they don't crash on a default Windows (cp1252) console.
_CHILD_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run_test_suite(test_file: Path, name: str) -> bool:
    """Run a single test file and return success status."""
    print(f"\n{'-' * 70}")
    print(f"Running: {name}")
    print(f"{'-' * 70}")

    result = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=str(project_root),
        capture_output=False,
        env=_CHILD_ENV,
    )

    return result.returncode == 0


def main():
    """Run all test suites."""
    print("=" * 70)
    print("  PHASE 3: Full Integration Testing")
    print("  Test Runner")
    print("=" * 70)
    
    test_suites = [
        # Smoke tests (quick validation)
        (project_root / "tests" / "smoke" / "test_core.py", "Smoke: Core Architecture"),
        (project_root / "tests" / "unit" / "test_config_unified.py", "Unit: Config Unification (ADR-0007)"),

        # Unit tests for each stage
        (project_root / "tests" / "unit" / "test_stage1_data_acquisition.py", "Unit: Stage 1 - Data Acquisition"),
        (project_root / "tests" / "unit" / "test_stage2_feature_extraction.py", "Unit: Stage 2 - Feature Extraction"),
        (project_root / "tests" / "unit" / "test_stage3_knowledge_graph.py", "Unit: Stage 3 - Knowledge Graph"),
        (project_root / "tests" / "unit" / "test_stage4_graph_embeddings.py", "Unit: Stage 4 - Graph Embeddings"),
        (project_root / "tests" / "unit" / "test_stage5_graphrag.py", "Unit: Stage 5 - GraphRAG"),
        (project_root / "tests" / "unit" / "test_stage6_threat_explanation.py", "Unit: Stage 6 - Threat Explanation"),
        
        # Integration tests
        (project_root / "tests" / "integration" / "test_adapters_integration.py", "Integration: Adapter Integration"),
    ]
    
    results = []
    
    for test_file, name in test_suites:
        if test_file.exists():
            success = run_test_suite(test_file, name)
            results.append((name, success))
        else:
            print(f"\n[SKIP] SKIPPED: {name} (file not found: {test_file})")
            results.append((name, None))
    
    # Print summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    total = len(results)
    
    for name, result in results:
        if result is True:
            status = "[PASS]"
        elif result is False:
            status = "[FAIL]"
        else:
            status = "[SKIP]"
        print(f"  {status}: {name}")

    print("\n" + "-" * 70)
    print(f"  Total: {passed} passed, {failed} failed, {skipped} skipped out of {total}")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
