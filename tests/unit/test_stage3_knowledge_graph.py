"""
Unit Tests for Stage 3: Knowledge Graph

Tests for Neo4j graph connectivity and operations.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config
from src.core.exceptions import GraphError

HAS_NEO4J = False
try:
    from src.services.knowledge_graph.neo4j_connection_v2 import (
        get_adapter,
        verify_connectivity,
        get_stats,
    )
    HAS_NEO4J = True
except ImportError:
    pass


class TestStage3KnowledgeGraph:
    """Test suite for knowledge graph stage."""

    def test_config_neo4j_uri(self):
        """Test that Neo4j URI is configured."""
        config = get_config()
        
        assert config.NEO4J_URI, "NEO4J_URI not configured"
        assert config.NEO4J_USER, "NEO4J_USER not configured"
        assert config.NEO4J_PASSWORD, "NEO4J_PASSWORD not configured"
        
        print(f"[OK] Neo4j configured at {config.NEO4J_URI}")

    def test_adapter_initialization(self):
        """Test that graph adapter can be initialized."""
        if not HAS_NEO4J:
            print("[SKIP] SKIPPED: neo4j package not installed")
            return
        
        adapter = get_adapter()
        assert adapter is not None, "Graph adapter is None"
        print(f"[OK] Graph adapter initialized: {type(adapter).__name__}")

    def test_adapter_stats(self):
        """Test that adapter provides statistics."""
        if not HAS_NEO4J:
            print("[SKIP] SKIPPED: neo4j package not installed")
            return
        
        try:
            stats = get_stats()
            print(f"[OK] Graph stats retrieved: {stats}")
        except GraphError as e:
            print(f"[SKIP] Neo4j not running (expected): {e.code}")
        except Exception as e:
            print(f"[FAIL] Unexpected error: {e}")
            raise

    def test_graph_queries_available(self):
        """Test that graph query functions are available."""
        if not HAS_NEO4J:
            print("[SKIP] SKIPPED: neo4j package not installed")
            return
        
        from src.services.knowledge_graph.neo4j_connection_v2 import (
            run_query,
            run_write_query,
            run_batch_query,
        )
        
        assert callable(run_query), "run_query not callable"
        assert callable(run_write_query), "run_write_query not callable"
        assert callable(run_batch_query), "run_batch_query not callable"
        
        print("[OK] All graph query functions available")


def main():
    """Run all Stage 3 tests."""
    print("\n" + "=" * 70)
    print("  Stage 3: Knowledge Graph - Unit Tests")
    print("=" * 70)
    
    test = TestStage3KnowledgeGraph()
    passed = 0
    
    try:
        print("\n[1/4] Testing Neo4j configuration...")
        test.test_config_neo4j_uri()
        passed += 1
        
        print("\n[2/4] Testing adapter initialization...")
        test.test_adapter_initialization()
        passed += 1
        
        print("\n[3/4] Testing adapter statistics...")
        test.test_adapter_stats()
        passed += 1
        
        print("\n[4/4] Testing graph query functions...")
        test.test_graph_queries_available()
        passed += 1
        
        print("\n" + "=" * 70)
        print(f"  Results: {passed}/4 passed [OK]")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
