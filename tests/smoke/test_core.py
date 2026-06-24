"""
Smoke test: Import integrity.

Dynamically imports all source modules to catch circular dependencies,
missing imports, and syntax errors.
"""

import sys
import importlib
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def test_import_integrity():
    """Import all source modules to validate basic integrity."""
    
    src_dir = project_root / "src"
    
    modules_to_import = [
        "src.core.exceptions",
        "src.core.config",
        "src.ports.llm_port",
        "src.ports.graph_port",
        "src.ports.embedding_port",
        "src.adapters.mock_llm_adapter",
        "src.adapters.mock_graph_adapter",
        "src.adapters.ollama_adapter",
        # Neo4j adapter requires neo4j package; skip if not available
    ]
    
    errors = []
    for module_name in modules_to_import:
        try:
            importlib.import_module(module_name)
            print(f"  [OK] {module_name}")
        except Exception as e:
            errors.append((module_name, str(e)))
            print(f"  [FAIL] {module_name}: {e}")
    
    if errors:
        raise AssertionError(f"Import failed for {len(errors)} module(s):\n" + 
                           "\n".join(f"  {m}: {e}" for m, e in errors))
    
    print(f"\nImport integrity: PASS ({len(modules_to_import)} modules)")


def test_exceptions_structured():
    """Verify exception hierarchy is structured correctly."""
    from src.core.exceptions import AppError, ValidationError, GraphError, LLMError
    
    # Test exception creation
    err = AppError(message="Test error")
    assert err.to_dict()["error"]["code"] == "APP_ERROR"
    
    config_err = ValidationError(
        message="Config failed",
        details={"key": "value"},
        recovery_hint="Fix the config",
    )
    assert config_err.to_dict()["error"]["recovery_hint"] == "Fix the config"
    
    print("Exception hierarchy: PASS")


def test_ports_are_abstract():
    """Verify ports cannot be instantiated directly."""
    from src.ports.llm_port import LLMPort
    from src.ports.graph_port import GraphPort
    
    try:
        llm = LLMPort()
        assert False, "LLMPort should not be instantiable"
    except TypeError:
        pass
    
    try:
        graph = GraphPort()
        assert False, "GraphPort should not be instantiable"
    except TypeError:
        pass
    
    print("Port abstraction: PASS")


def test_adapters_implement_ports():
    """Verify adapters implement their ports correctly."""
    from src.ports.llm_port import LLMPort
    from src.ports.graph_port import GraphPort
    from src.adapters.mock_llm_adapter import MockLLMAdapter
    from src.adapters.mock_graph_adapter import MockGraphAdapter
    
    llm = MockLLMAdapter()
    assert isinstance(llm, LLMPort)
    assert hasattr(llm, 'generate')
    assert hasattr(llm, 'get_stats')
    
    graph = MockGraphAdapter()
    assert isinstance(graph, GraphPort)
    assert hasattr(graph, 'run_query')
    assert hasattr(graph, 'verify_connectivity')
    
    print("Adapter contracts: PASS")


def test_mock_adapters_functional():
    """Smoke test mock adapters."""
    from src.adapters.mock_llm_adapter import MockLLMAdapter
    from src.adapters.mock_graph_adapter import MockGraphAdapter
    
    # Test LLM
    llm = MockLLMAdapter()
    response = llm.generate("What is a DDoS attack?")
    assert isinstance(response, str)
    assert len(response) > 0
    assert llm.request_count == 1
    assert llm.get_model_name() == "mock-llm"
    
    # Test Graph
    graph = MockGraphAdapter()
    assert graph.verify_connectivity() is True
    
    results = graph.run_query("MATCH (n) RETURN count(n)")
    assert len(results) > 0
    
    stats = graph.get_stats()
    assert stats["node_count"] == 5500000
    
    print("Mock adapters functional: PASS")


if __name__ == "__main__":
    print("=" * 60)
    print("  Smoke Test Suite")
    print("=" * 60)
    
    tests = [
        test_import_integrity,
        test_exceptions_structured,
        test_ports_are_abstract,
        test_adapters_implement_ports,
        test_mock_adapters_functional,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test_func.__name__}: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)
