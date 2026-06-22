"""
Performance Benchmarks

Measures execution time for key operations using mock adapters.
Useful for profiling and detecting performance regressions.
"""

import sys
import time
from pathlib import Path
from typing import List, Tuple

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import get_config
from src.adapters.mock_llm_adapter import MockLLMAdapter
from src.adapters.mock_graph_adapter import MockGraphAdapter
from src.adapters.embedding_adapter import MockEmbeddingAdapter


class PerformanceBenchmarks:
    """Performance benchmarking suite."""

    def __init__(self):
        self.results: List[Tuple[str, float]] = []
        self.config = get_config()

    def benchmark_llm_generation(self, prompts_count: int = 100) -> float:
        """Benchmark LLM generation speed."""
        llm = MockLLMAdapter()
        prompts = [
            "What is the threat level?",
            "Summarize the attack",
            "List IoT devices",
        ] * (prompts_count // 3)
        
        start = time.time()
        for prompt in prompts:
            _ = llm.generate(prompt)
        elapsed = time.time() - start
        
        ops_per_sec = len(prompts) / elapsed
        self.results.append(("LLM generation", elapsed))
        
        print(f"✓ LLM: Generated {len(prompts)} texts in {elapsed:.2f}s ({ops_per_sec:.0f} ops/sec)")
        return elapsed

    def benchmark_embedding_generation(self, texts_count: int = 1000) -> float:
        """Benchmark embedding generation speed."""
        embedding = MockEmbeddingAdapter()
        texts = [
            "Device performing DDoS attack",
            "Benign traffic from sensor",
            "Suspicious C&C communication",
        ] * (texts_count // 3)
        
        start = time.time()
        embeddings = embedding.embed_texts(texts)
        elapsed = time.time() - start
        
        ops_per_sec = len(texts) / elapsed
        self.results.append(("Embedding generation", elapsed))
        
        print(f"✓ Embeddings: Generated {len(embeddings)} embeddings in {elapsed:.2f}s ({ops_per_sec:.0f} ops/sec)")
        return elapsed

    def benchmark_graph_queries(self, query_count: int = 1000) -> float:
        """Benchmark graph query speed."""
        graph = MockGraphAdapter()
        queries = [
            "MATCH (d:Device) WHERE d.role = 'gateway' RETURN d LIMIT 10",
            "MATCH (d1)-[:COMMUNICATES_WITH]->(d2) RETURN d1, d2 LIMIT 50",
            "MATCH (d:Device)-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType) RETURN d, f, a",
        ] * (query_count // 3)
        
        start = time.time()
        for query in queries:
            _ = graph.run_query(query)
        elapsed = time.time() - start
        
        ops_per_sec = len(queries) / elapsed
        self.results.append(("Graph queries", elapsed))
        
        print(f"✓ Graph: Executed {len(queries)} queries in {elapsed:.2f}s ({ops_per_sec:.0f} ops/sec)")
        return elapsed

    def benchmark_config_initialization(self, iterations: int = 1000) -> float:
        """Benchmark config initialization."""
        start = time.time()
        for _ in range(iterations):
            config = get_config()
        elapsed = time.time() - start
        
        ops_per_sec = iterations / elapsed
        self.results.append(("Config init", elapsed))
        
        print(f"✓ Config: Initialized {iterations} times in {elapsed:.2f}s ({ops_per_sec:.0f} ops/sec)")
        return elapsed

    def benchmark_adapter_initialization(self, iterations: int = 1000) -> float:
        """Benchmark adapter initialization."""
        start = time.time()
        for _ in range(iterations):
            llm = MockLLMAdapter()
            graph = MockGraphAdapter()
            embedding = MockEmbeddingAdapter()
        elapsed = time.time() - start
        
        ops_per_sec = (iterations * 3) / elapsed
        self.results.append(("Adapter init", elapsed))
        
        print(f"✓ Adapters: Initialized {iterations * 3} adapters in {elapsed:.2f}s ({ops_per_sec:.0f} ops/sec)")
        return elapsed

    def benchmark_end_to_end_pipeline(self, iterations: int = 10) -> float:
        """Benchmark full end-to-end pipeline."""
        llm = MockLLMAdapter()
        graph = MockGraphAdapter()
        embedding = MockEmbeddingAdapter()
        
        start = time.time()
        for i in range(iterations):
            # Simulate pipeline: query → embed → explain
            devices = graph.run_query("MATCH (d:Device) RETURN d LIMIT 10")
            descriptions = [f"Device {j}" for j in range(len(devices))]
            embeddings = embedding.embed_texts(descriptions)
            explanation = llm.generate("Analyze threats")
        
        elapsed = time.time() - start
        ops_per_sec = iterations / elapsed
        self.results.append(("End-to-end pipeline", elapsed))
        
        print(f"✓ E2E: Completed {iterations} pipeline iterations in {elapsed:.2f}s ({ops_per_sec:.1f} iter/sec)")
        return elapsed

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 70)
        print("  Benchmark Summary")
        print("=" * 70)
        
        total_time = sum(elapsed for _, elapsed in self.results)
        
        print(f"\n{'Operation':<30} {'Time (s)':<12} {'% of Total':<10}")
        print("─" * 70)
        
        for op_name, elapsed in sorted(self.results, key=lambda x: x[1], reverse=True):
            pct = (elapsed / total_time * 100) if total_time > 0 else 0
            print(f"{op_name:<30} {elapsed:<12.4f} {pct:<10.1f}%")
        
        print("─" * 70)
        print(f"{'Total':<30} {total_time:<12.4f} {'100.0':<10}%")
        print("=" * 70)


def main():
    """Run all benchmarks."""
    print("\n" + "=" * 70)
    print("  Performance Benchmarks (Mock Adapters)")
    print("=" * 70)
    
    bench = PerformanceBenchmarks()
    
    print("\n[1/6] Benchmarking config initialization...")
    bench.benchmark_config_initialization(1000)
    
    print("\n[2/6] Benchmarking adapter initialization...")
    bench.benchmark_adapter_initialization(100)
    
    print("\n[3/6] Benchmarking LLM generation...")
    bench.benchmark_llm_generation(100)
    
    print("\n[4/6] Benchmarking embedding generation...")
    bench.benchmark_embedding_generation(500)
    
    print("\n[5/6] Benchmarking graph queries...")
    bench.benchmark_graph_queries(500)
    
    print("\n[6/6] Benchmarking end-to-end pipeline...")
    bench.benchmark_end_to_end_pipeline(10)
    
    bench.print_summary()


if __name__ == "__main__":
    main()
