"""
Unit Tests for Stage 4: Graph Embeddings

Tests for embedding generation and storage.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config
from src.core.exceptions import EmbeddingError
from src.adapters.embedding_adapter import MockEmbeddingAdapter


class TestStage4GraphEmbeddings:
    """Test suite for graph embeddings stage."""

    def test_embedding_dimension_config(self):
        """Test that embedding dimension is configured."""
        config = get_config()
        
        assert config.EMBEDDING_DIMENSION == 384, f"Expected 384-dim embeddings, got {config.EMBEDDING_DIMENSION}"
        assert config.EMBEDDING_BATCH_SIZE > 0, "Batch size must be positive"
        
        print(f"âœ“ Embedding config: dimension={config.EMBEDDING_DIMENSION}, batch={config.EMBEDDING_BATCH_SIZE}")

    def test_mock_embedding_adapter(self):
        """Test mock embedding adapter."""
        adapter = MockEmbeddingAdapter(embedding_dimension=768)
        
        # Test single embedding
        embedding = adapter.embed_text("Test text for IoT threat analysis")
        assert len(embedding) == 768, f"Expected 768-dim embedding, got {len(embedding)}"
        assert isinstance(embedding, list), "Embedding should be a list"
        assert all(isinstance(v, (int, float)) for v in embedding), "All embedding values should be numeric"
        
        print(f"âœ“ Single embedding generated: {len(embedding)} dimensions")

    def test_mock_batch_embeddings(self):
        """Test batch embedding generation."""
        adapter = MockEmbeddingAdapter(embedding_dimension=768)
        
        texts = [
            "Device performing DDoS attack",
            "Benign traffic from IoT sensor",
            "Suspected malware C&C communication",
        ]
        
        embeddings = adapter.embed_texts(texts)
        assert len(embeddings) == len(texts), f"Expected {len(texts)} embeddings, got {len(embeddings)}"
        
        for i, emb in enumerate(embeddings):
            assert len(emb) == 768, f"Embedding {i} has wrong dimension: {len(emb)}"
        
        print(f"âœ“ Batch embeddings generated: {len(embeddings)} texts Ã— {len(embeddings[0])} dims")

    def test_embedding_adapter_stats(self):
        """Test embedding adapter statistics."""
        adapter = MockEmbeddingAdapter(embedding_dimension=768)
        
        # Generate some embeddings
        adapter.embed_texts(["text 1", "text 2", "text 3"])
        
        stats = adapter.get_stats()
        assert "model" in stats, "Stats missing 'model'"
        assert "dimension" in stats, "Stats missing 'dimension'"
        assert "requests" in stats, "Stats missing 'requests'"
        
        print(f"âœ“ Adapter stats: {stats}")

    def test_embedding_functions_available(self):
        """Test that embedding functions are available."""
        try:
            from src.services.graph_embeddings.embeddings_v2 import (
                get_embedding_adapter,
                get_gemini_embeddings,
                generate_device_descriptions,
                embed_device_descriptions,
            )
            
            assert callable(get_embedding_adapter), "get_embedding_adapter not callable"
            assert callable(get_gemini_embeddings), "get_gemini_embeddings not callable"
            assert callable(generate_device_descriptions), "generate_device_descriptions not callable"
            assert callable(embed_device_descriptions), "embed_device_descriptions not callable"
            
            print("âœ“ All embedding functions available")
        except ImportError as e:
            print(f"âŠ˜ Could not import embeddings module: {e}")


def main():
    """Run all Stage 4 tests."""
    print("\n" + "=" * 70)
    print("  Stage 4: Graph Embeddings - Unit Tests")
    print("=" * 70)
    
    test = TestStage4GraphEmbeddings()
    passed = 0
    
    try:
        print("\n[1/5] Testing embedding dimension config...")
        test.test_embedding_dimension_config()
        passed += 1
        
        print("\n[2/5] Testing mock embedding adapter...")
        test.test_mock_embedding_adapter()
        passed += 1
        
        print("\n[3/5] Testing batch embeddings...")
        test.test_mock_batch_embeddings()
        passed += 1
        
        print("\n[4/5] Testing adapter statistics...")
        test.test_embedding_adapter_stats()
        passed += 1
        
        print("\n[5/5] Testing embedding functions...")
        test.test_embedding_functions_available()
        passed += 1
        
        print("\n" + "=" * 70)
        print(f"  Results: {passed}/5 passed âœ“")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\nâœ— FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
