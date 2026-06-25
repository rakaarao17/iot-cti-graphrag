"""Unit test: configuration is unified (ADR-0007), no services required.

Verifies that config/settings.py and src.core.config.Config expose identical
values for every shared key (single source of truth), and that those values
match the ones the evaluation pipeline actually ran with -- so the unification
introduces zero result-affecting drift.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config
from config import settings


SHARED_KEYS = [
    "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE",
    "NEO4J_MAX_RETRIES", "OLLAMA_ENDPOINT", "OLLAMA_MODEL",
    "EMBEDDING_DIMENSION", "EMBEDDING_BATCH_SIZE",
    "LLM_TEMPERATURE", "LLM_MAX_TOKENS", "LOG_LEVEL",
    "DATA_RAW_DIR", "DATA_PROCESSED_DIR", "DATA_SAMPLES_DIR",
]

# The values the evaluation pipeline was run with (previously only in settings.py).
PROVEN = {
    "OLLAMA_MODEL": "gemma4:e2b",
    "LLM_TEMPERATURE": 0.3,
    "LLM_MAX_TOKENS": 4096,
    "EMBEDDING_DIMENSION": 384,
    "OLLAMA_ENDPOINT": "http://localhost:11434/api/generate",
}


def test_settings_match_canonical_config():
    cfg = get_config()
    mismatches = []
    for key in SHARED_KEYS:
        s = getattr(settings, key)
        c = getattr(cfg, key)
        if s != c:
            mismatches.append(f"{key}: settings={s!r} != Config={c!r}")
    assert not mismatches, "Config not unified:\n  " + "\n  ".join(mismatches)
    print(f"[OK] {len(SHARED_KEYS)} shared keys identical across settings and Config")


def test_proven_values_preserved():
    cfg = get_config()
    bad = []
    for key, expected in PROVEN.items():
        got = getattr(cfg, key)
        if got != expected:
            bad.append(f"{key}: expected {expected!r}, got {got!r}")
    assert not bad, "Proven pipeline values changed (would invalidate results):\n  " + "\n  ".join(bad)
    print(f"[OK] {len(PROVEN)} proven pipeline values preserved (temp=0.3, tokens=4096, gemma4:e2b)")


def test_pipeline_only_constants_present():
    # settings must still expose the pipeline-only names callers rely on
    for name in ["logger", "NODE2VEC_DIMENSIONS", "DEFAULT_SAMPLE_SIZE",
                 "TOP_K_RESULTS", "SENTENCE_TRANSFORMER_MODEL", "NEO4J_BATCH_SIZE"]:
        assert hasattr(settings, name), f"settings.{name} missing after unification"
    print("[OK] pipeline-only constants still exported by settings")


if __name__ == "__main__":
    test_settings_match_canonical_config()
    test_proven_values_preserved()
    test_pipeline_only_constants_present()
    print("\nResults: 3 passed, 0 failed")
