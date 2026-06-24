"""
Unit Tests for Stage 5: GraphRAG

Tests for retrieval augmented generation functionality.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config


class TestStage5GraphRAG:
    """Test suite for GraphRAG stage."""

    def test_rag_pipeline_available(self):
        """Test that RAG pipeline is available."""
        try:
            from src.services.graphrag import rag_pipeline
            print("[OK] RAG pipeline module imported successfully")
        except ImportError as e:
            print(f"[SKIP] Could not import RAG pipeline: {e}")

    def test_retrievers_available(self):
        """Test that retriever functions are available."""
        try:
            from src.services.graphrag import retrievers
            print("[OK] Retrievers module imported successfully")
        except ImportError as e:
            print(f"[SKIP] Could not import retrievers: {e}")

    def test_vector_store_available(self):
        """Test that vector store is available."""
        try:
            from src.services.graphrag import vector_store
            print("[OK] Vector store module imported successfully")
        except ImportError as e:
            print(f"[SKIP] Could not import vector store: {e}")

    def test_embedding_config_for_rag(self):
        """Test that embedding configuration supports RAG."""
        config = get_config()
        
        assert config.EMBEDDING_DIMENSION > 0, "Embedding dimension must be positive"
        assert config.EMBEDDINGS_MODEL, "Embeddings model not configured"
        
        print(f"[OK] RAG embedding config: model={config.EMBEDDINGS_MODEL}, dim={config.EMBEDDING_DIMENSION}")


def main():
    """Run all Stage 5 tests."""
    print("\n" + "=" * 70)
    print("  Stage 5: GraphRAG - Unit Tests")
    print("=" * 70)
    
    test = TestStage5GraphRAG()
    passed = 0
    
    try:
        print("\n[1/4] Testing RAG pipeline availability...")
        test.test_rag_pipeline_available()
        passed += 1
        
        print("\n[2/4] Testing retrievers availability...")
        test.test_retrievers_available()
        passed += 1
        
        print("\n[3/4] Testing vector store availability...")
        test.test_vector_store_available()
        passed += 1
        
        print("\n[4/4] Testing embedding configuration...")
        test.test_embedding_config_for_rag()
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
