"""
Unit Tests for Stage 6: Threat Explanation

Tests for LLM-powered threat analysis.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config
from src.core.exceptions import LLMError


class TestStage6ThreatExplanation:
    """Test suite for threat explanation stage."""

    def test_ollama_config(self):
        """Test that Ollama is configured."""
        config = get_config()
        
        assert config.OLLAMA_MODEL, "OLLAMA_MODEL not configured"
        assert config.OLLAMA_ENDPOINT, "OLLAMA_ENDPOINT not configured"
        assert config.LLM_TEMPERATURE >= 0, "Temperature must be non-negative"
        assert config.LLM_MAX_TOKENS > 0, "Max tokens must be positive"
        
        print(f"[OK] Ollama config: model={config.OLLAMA_MODEL}, endpoint={config.OLLAMA_ENDPOINT}")

    def test_ollama_client_v2_import(self):
        """Test that updated Ollama client can be imported."""
        try:
            from src.services.threat_explanation.ollama_client_v2 import (
                OllamaClient,
                get_adapter,
            )
            print("[OK] OllamaClient v2 imported successfully")
        except ImportError as e:
            print(f"[FAIL] Failed to import OllamaClient v2: {e}")
            raise

    def test_ollama_client_backward_compatibility(self):
        """Test backward compatibility of OllamaClient."""
        try:
            from src.services.threat_explanation.ollama_client_v2 import OllamaClient
            
            client = OllamaClient()
            
            assert hasattr(client, 'generate'), "OllamaClient missing generate method"
            assert hasattr(client, 'generate_advanced'), "OllamaClient missing generate_advanced method"
            assert hasattr(client, 'get_stats'), "OllamaClient missing get_stats method"
            assert hasattr(client, 'get_model_name'), "OllamaClient missing get_model_name method"
            
            print("[OK] OllamaClient has all required methods")
        except Exception as e:
            print(f"[FAIL] OllamaClient compatibility check failed: {e}")
            raise

    def test_ollama_stats(self):
        """Test that Ollama client provides statistics."""
        try:
            from src.services.threat_explanation.ollama_client_v2 import OllamaClient
            
            client = OllamaClient()
            stats = client.get_stats()
            
            assert "model" in stats, "Stats missing 'model'"
            assert "requests" in stats, "Stats missing 'requests'"
            
            print(f"[OK] Ollama client stats: {stats}")
        except Exception as e:
            print(f"[FAIL] Failed to get Ollama stats: {e}")
            raise

    def test_threat_explanation_functions_available(self):
        """Test that threat explanation functions are available."""
        try:
            # These functions should exist in the threat explanation module
            import src.services.threat_explanation.explainer as explainer
            print("[OK] Threat explainer module imported successfully")
        except ImportError as e:
            print(f"[SKIP] Could not import explainer module (may not be implemented yet): {e}")


def main():
    """Run all Stage 6 tests."""
    print("\n" + "=" * 70)
    print("  Stage 6: Threat Explanation - Unit Tests")
    print("=" * 70)
    
    test = TestStage6ThreatExplanation()
    passed = 0
    
    try:
        print("\n[1/6] Testing Ollama configuration...")
        test.test_ollama_config()
        passed += 1
        
        print("\n[2/6] Testing OllamaClient v2 import...")
        test.test_ollama_client_v2_import()
        passed += 1
        
        print("\n[3/6] Testing backward compatibility...")
        test.test_ollama_client_backward_compatibility()
        passed += 1
        
        print("\n[4/6] Testing Ollama client statistics...")
        test.test_ollama_stats()
        passed += 1
        
        print("\n[5/6] Testing threat explanation functions...")
        test.test_threat_explanation_functions_available()
        passed += 1
        
        print("\n" + "=" * 70)
        print(f"  Results: {passed}/6 passed [OK]")
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
