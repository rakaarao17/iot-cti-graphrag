"""
Integration Tests for Stage Adapters

Tests that the new adapters work correctly with stage modules
and that backward compatibility is maintained.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config
from src.core.exceptions import GraphError, LLMError, EmbeddingError
from src.adapters.ollama_adapter import OllamaAdapter
from src.adapters.embedding_adapter import MockEmbeddingAdapter

# Try to import Neo4j adapter, skip if neo4j package not installed
try:
    from src.adapters.neo4j_adapter import Neo4jAdapter
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    print("Warning: neo4j package not installed, skipping Neo4j adapter tests")


def test_neo4j_adapter_import():
    """Test that Neo4j adapter can be imported and instantiated."""
    print("\n[1/5] Testing Neo4j adapter import...")
    if not HAS_NEO4J:
        print(f"  [SKIP] SKIPPED: neo4j package not installed")
        return True  # Skip but don't fail
    
    try:
        config = get_config()
        adapter = Neo4jAdapter(
            uri=config.NEO4J_URI,
            user=config.NEO4J_USER,
            password=config.NEO4J_PASSWORD,
        )
        print(f"  [OK] Neo4j adapter initialized for {config.NEO4J_URI}")
        stats = adapter.get_stats()
        print(f"  [OK] Stats: {stats}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_ollama_adapter_initialization():
    """Test that Ollama adapter initializes correctly."""
    print("\n[2/5] Testing Ollama adapter initialization...")
    try:
        config = get_config()
        adapter = OllamaAdapter(
            endpoint=config.OLLAMA_ENDPOINT,
            model=config.OLLAMA_MODEL,
        )
        print(f"  [OK] Ollama adapter initialized for {config.OLLAMA_MODEL}")
        model_name = adapter.get_model_name()
        print(f"  [OK] Model: {model_name}")
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_embedding_adapter_mock():
    """Test embedding adapter (mock version)."""
    print("\n[3/5] Testing embedding adapter (mock)...")
    try:
        adapter = MockEmbeddingAdapter(embedding_dimension=768)
        
        # Test single embedding
        embedding = adapter.embed_text("Test text")
        assert len(embedding) == 768, f"Expected 768-dim embedding, got {len(embedding)}"
        print(f"  [OK] Single text embedding: {len(embedding)} dimensions")
        
        # Test batch embedding
        embeddings = adapter.embed_texts(["Text 1", "Text 2", "Text 3"])
        assert len(embeddings) == 3, f"Expected 3 embeddings, got {len(embeddings)}"
        assert len(embeddings[0]) == 768, f"Expected 768-dim, got {len(embeddings[0])}"
        print(f"  [OK] Batch embeddings: {len(embeddings)} texts, {len(embeddings[0])} dimensions each")
        
        return True
    except AssertionError as e:
        print(f"  [FAIL] FAILED: {e}")
        return False
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        return False


def test_stage3_neo4j_connection_import():
    """Test that stage3's neo4j_connection module imports and works."""
    print("\n[4/5] Testing stage3 neo4j_connection import...")
    if not HAS_NEO4J:
        print(f"  [SKIP] SKIPPED: neo4j package not installed")
        return True  # Skip but don't fail
    
    try:
        from src.services.knowledge_graph.neo4j_connection import (
            verify_connectivity,
            run_query,
            get_database_stats,
        )
        print(f"  [OK] All functions imported successfully")

        # Test connectivity + stats (should not raise)
        try:
            connected = verify_connectivity()
            print(f"  [OK] verify_connectivity() = {connected}")
            stats = get_database_stats()
            print(f"  [OK] Got stats: {stats}")
        except GraphError as e:
            # Expected if Neo4j is not running
            print(f"  [OK] GraphError raised as expected (Neo4j may not be running): {e.code}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stage6_ollama_client_v2_import():
    """Test that stage6's ollama_client_v2 can be imported."""
    print("\n[5/5] Testing stage6 ollama_client_v2 import...")
    try:
        from src.services.threat_explanation.ollama_client_v2 import (
            OllamaClient,
            get_adapter,
        )
        print(f"  [OK] All functions imported successfully")
        
        # Test backward compatibility
        client = OllamaClient()
        print(f"  [OK] OllamaClient instantiated (backward compatible)")
        print(f"  [OK] Model: {client.model}")
        print(f"  [OK] Endpoint: {client.endpoint}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("  Integration Tests for Stage Adapters")
    print("=" * 70)

    results = [
        test_neo4j_adapter_import(),
        test_ollama_adapter_initialization(),
        test_embedding_adapter_mock(),
        test_stage3_neo4j_connection_import(),
        test_stage6_ollama_client_v2_import(),
    ]

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"  Results: {passed}/{total} passed")
    print("=" * 70)

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
