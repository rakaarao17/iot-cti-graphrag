# Plan: Local LLM Comparison for IoT CTI Pipeline (Base vs Fine-Tuned)
# Branch: feature/llm-comparison
# Date: 2026-06-21

## Goal

Add an experimental comparison layer that runs three local Ollama models — Gemma 4 2B,
Phi-3 base, and Phi-3 fine-tuned on CICIoT — against identical GraphRAG-retrieved context
and measures latency, grounding ratio, and explanation quality. Research question: does
domain-specific fine-tuning (zeroday-phi3-ciciot-v2) improve threat explanation quality
over base models when all receive the same structured graph context?

## Global Constraints

- Python ≥3.11
- Models (all local via Ollama): `gemma4:e2b`, `phi3:latest`, `zeroday-phi3-ciciot-v2:latest`
- No Gemini API — fully offline, no API keys required
- All models receive IDENTICAL retrieved context — retrieval runs once, output is cached
- Temperature = 0.0 for all models (reproducibility)
- Max output tokens = 512 for all models
- Grounding check reuses existing `check_grounding()` from `src/services/threat_explanation/grounding.py`
- Existing pipeline (extraction → ingestion → retrieval → explainer) is NOT modified
- `google-generativeai>=0.7` added to `requirements.txt`
- All new code under `src/adapters/` and `src/services/evaluation/`
- Scripts under `scripts/`
- Tests: unit tests mock HTTP; no real API calls in test suite

## Architecture

```
[comparison_benchmark.json]  ←  20 seed queries (5 categories × 4)
         ↓
[GraphRAG retrieval]  →  [retrieval_cache.json]  (frozen; same for all models)
         ↓
[run_comparison.py]
    ├─ GeminiAdapter     → gemini-1.5-flash
    ├─ OllamaAdapter     → gemma4:e2b
    └─ OllamaAdapter     → phi3:latest
         ↓
[ModelComparisonResult]  →  [comparison_report.json + comparison_report.md]
```

## File Structure

```
src/adapters/
  llm_adapters.py          # LLMAdapter Protocol + GeminiAdapter + OllamaAdapter

src/services/evaluation/
  llm_comparison.py        # ModelComparisonResult, run_model_comparison()
  comparison_report.py     # generate_comparison_report() → JSON + MD

data/eval/
  comparison_benchmark.json   # 20 seed queries
  retrieval_cache.json         # written by scripts/cache_retrieval.py
  comparison_report.json       # written by scripts/run_comparison.py
  comparison_report.md         # written by scripts/run_comparison.py

scripts/
  cache_retrieval.py       # pre-fetches GraphRAG context for all benchmark queries
  run_comparison.py        # main CLI: runs all 3 models, writes report
```

---

## Task 1: Unified LLM Adapter Interface (GeminiAdapter + OllamaAdapter)

### Files

**New:** `src/adapters/llm_adapters.py`
**Modify:** `requirements.txt` (add `google-generativeai>=0.7`)
**New:** `tests/unit/test_llm_adapters.py`

### Specification

#### `LLMAdapter` Protocol

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LLMAdapter(Protocol):
    model_name: str          # e.g. "gemini-1.5-flash", "gemma4:e2b", "phi3:latest"
    deployment: str          # "cloud" | "local"

    def generate(self, prompt: str, context: str) -> "LLMResponse":
        ...
```

#### `LLMResponse` dataclass

```python
@dataclass
class LLMResponse:
    model_name: str
    deployment: str        # "cloud" | "local"
    prompt: str
    context: str
    response_text: str
    latency_ms: float
    input_tokens: int      # estimated: len(prompt+context) // 4
    output_tokens: int     # estimated: len(response_text) // 4
    error: Optional[str] = None   # None on success
```

Token counts are estimates (character count // 4) since local models don't return counts.

#### `GeminiAdapter`

```python
class GeminiAdapter:
    model_name = "gemini-1.5-flash"
    deployment = "cloud"

    def __init__(self, api_key: Optional[str] = None):
        # api_key defaults to os.environ["GOOGLE_API_KEY"]
        # raises ValueError with clear message if key is absent
        import google.generativeai as genai
        key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        if not key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Get a key at https://aistudio.google.com/app/apikey"
            )
        genai.configure(api_key=key)
        self._model = genai.GenerativeModel(
            self.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=512,
            )
        )

    def generate(self, prompt: str, context: str) -> LLMResponse:
        full_prompt = _build_prompt(prompt, context)
        t0 = time.perf_counter()
        try:
            resp = self._model.generate_content(full_prompt)
            text = resp.text
            error = None
        except Exception as e:
            text = ""
            error = str(e)
        latency_ms = (time.perf_counter() - t0) * 1000
        return LLMResponse(
            model_name=self.model_name,
            deployment=self.deployment,
            prompt=prompt,
            context=context,
            response_text=text,
            latency_ms=latency_ms,
            input_tokens=len(full_prompt) // 4,
            output_tokens=len(text) // 4,
            error=error,
        )
```

#### `OllamaAdapter`

```python
class OllamaAdapter:
    deployment = "local"

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self._base_url = base_url.rstrip("/")

    def generate(self, prompt: str, context: str) -> LLMResponse:
        full_prompt = _build_prompt(prompt, context)
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 512},
        }
        t0 = time.perf_counter()
        try:
            r = requests.post(
                f"{self._base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            r.raise_for_status()
            text = r.json().get("response", "")
            error = None
        except Exception as e:
            text = ""
            error = str(e)
        latency_ms = (time.perf_counter() - t0) * 1000
        return LLMResponse(
            model_name=self.model_name,
            deployment=self.deployment,
            prompt=prompt,
            context=context,
            response_text=text,
            latency_ms=latency_ms,
            input_tokens=len(full_prompt) // 4,
            output_tokens=len(text) // 4,
            error=error,
        )
```

#### `_build_prompt` helper (module-private)

```python
def _build_prompt(prompt: str, context: str) -> str:
    return (
        "You are a cybersecurity analyst. Use ONLY the provided context to answer.\n"
        "Do not use knowledge outside the context. If the context is insufficient, say so.\n\n"
        f"### Context\n{context}\n\n"
        f"### Question\n{prompt}\n\n"
        "### Answer"
    )
```

### Tests (`tests/unit/test_llm_adapters.py`)

Use `unittest.mock.patch` — no real API calls.

```python
def test_ollama_adapter_returns_llm_response():
    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"response": "test answer"}
        mock_post.return_value.raise_for_status = lambda: None
        adapter = OllamaAdapter("phi3:latest")
        result = adapter.generate("What is this attack?", "Flow: 192.168.1.1")
    assert isinstance(result, LLMResponse)
    assert result.model_name == "phi3:latest"
    assert result.deployment == "local"
    assert result.response_text == "test answer"
    assert result.latency_ms >= 0
    assert result.error is None

def test_ollama_adapter_captures_error():
    with patch("requests.post", side_effect=ConnectionError("refused")):
        adapter = OllamaAdapter("gemma4:e2b")
        result = adapter.generate("test", "ctx")
    assert result.response_text == ""
    assert "refused" in result.error

def test_gemini_adapter_raises_without_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            GeminiAdapter()

def test_gemini_adapter_generate(monkeypatch):
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value.generate_content.return_value.text = "gemini answer"
    mock_genai.types.GenerationConfig = MagicMock()
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
        adapter = GeminiAdapter(api_key="fake-key")
        result = adapter.generate("test prompt", "test context")
    assert result.response_text == "gemini answer"
    assert result.deployment == "cloud"
    assert result.error is None

def test_llm_response_protocol():
    adapter = OllamaAdapter("phi3:latest")
    assert isinstance(adapter, LLMAdapter)
```

5 tests total. TDD required: write tests first, then implementation.

---

## Task 2: Comparison Runner + CLI Script

### Files

**New:** `src/services/evaluation/llm_comparison.py`
**New:** `scripts/run_comparison.py`
**New:** `tests/unit/test_llm_comparison.py`

### Specification

#### `ModelComparisonResult` dataclass

```python
@dataclass
class ModelComparisonResult:
    query_id: str
    query: str
    context: str                          # the retrieved context passed to all models
    responses: Dict[str, LLMResponse]     # model_name → LLMResponse
    grounding: Dict[str, GroundingResult] # model_name → GroundingResult
```

#### `run_model_comparison()`

```python
def run_model_comparison(
    queries: List[Dict],                  # each: {id, query, context}
    adapters: List[LLMAdapter],
) -> List[ModelComparisonResult]:
    """
    Run all adapters against each query+context pair.
    Same context is passed to every adapter for each query.
    Returns one ModelComparisonResult per query.
    """
```

Implementation notes:
- For each query, for each adapter: call `adapter.generate(query["query"], query["context"])`
- Then call `check_grounding(response.response_text, query["context"])` for each response
- Collect into `ModelComparisonResult`
- Log progress: `print(f"[{i+1}/{len(queries)}] {query['id']}")`

#### `scripts/run_comparison.py`

CLI with argparse:

```
python scripts/run_comparison.py \
    --benchmark data/eval/comparison_benchmark.json \
    --retrieval-cache data/eval/retrieval_cache.json \
    --output-dir data/eval \
    --models gemini phi3 gemma   # optional: defaults to all 3
    --skip-gemini                # skip Gemini if no API key
```

Behaviour:
1. Load benchmark queries from `--benchmark`
2. Load retrieval cache from `--retrieval-cache` (a JSON mapping `query_id → context_text`)
3. Merge: attach `context` field to each query from the cache; skip queries with no cache entry (warn)
4. Build adapters: `GeminiAdapter()` (unless `--skip-gemini`), `OllamaAdapter("gemma4:e2b")`, `OllamaAdapter("phi3:latest")`
5. Call `run_model_comparison(queries, adapters)`
6. Call `generate_comparison_report(results, output_dir)` (Task 3)
7. Print summary table to console

If `--skip-gemini` and `GOOGLE_API_KEY` is absent, skip Gemini automatically with a warning instead of crashing.

### Tests (`tests/unit/test_llm_comparison.py`)

```python
def make_mock_adapter(name: str, deployment: str, response: str) -> LLMAdapter:
    """Return a minimal mock adapter."""

def test_run_model_comparison_returns_one_result_per_query():
    adapters = [make_mock_adapter("m1", "local", "answer1"),
                make_mock_adapter("m2", "cloud", "answer2")]
    queries = [
        {"id": "q1", "query": "What attack?", "context": "192.168.1.1 DDoS"},
        {"id": "q2", "query": "Which MITRE?", "context": "T1046 scan"},
    ]
    results = run_model_comparison(queries, adapters)
    assert len(results) == 2
    assert results[0].query_id == "q1"
    assert set(results[0].responses.keys()) == {"m1", "m2"}

def test_run_model_comparison_grounding_computed():
    adapter = make_mock_adapter("m1", "local", "192.168.1.1 attacked via DDoS")
    queries = [{"id": "q1", "query": "test", "context": "192.168.1.1 DDoS"}]
    results = run_model_comparison(queries, [adapter])
    assert "m1" in results[0].grounding
    gr = results[0].grounding["m1"]
    assert gr.grounding_ratio >= 0.0

def test_run_model_comparison_captures_adapter_error():
    # adapter that raises on generate()
    ...
    results = run_model_comparison(queries, [error_adapter])
    assert results[0].responses["error_model"].error is not None

def test_run_model_comparison_empty_queries():
    results = run_model_comparison([], [make_mock_adapter("m1", "local", "x")])
    assert results == []
```

4 tests total. TDD required.

---

## Task 3: Benchmark Queries + Comparison Report Generator

### Files

**New:** `data/eval/comparison_benchmark.json`
**New:** `src/services/evaluation/comparison_report.py`
**New:** `tests/unit/test_comparison_report.py`

### Specification

#### `data/eval/comparison_benchmark.json`

20 queries, 4 per category. Schema:

```json
[
  {
    "id": "te-01",
    "category": "threat_explanation",
    "query": "Explain the attack behavior observed in these network flows.",
    "expected_entities": ["DDoS", "UDP", "flood"],
    "retrieval_type": "combined"
  },
  ...
]
```

Categories (4 queries each):
- `threat_explanation` — ids: te-01 to te-04
- `incident_summary` — ids: is-01 to is-04
- `attack_classification` — ids: ac-01 to ac-04
- `analyst_qa` — ids: aq-01 to aq-04
- `executive_summary` — ids: es-01 to es-04

Queries must be generic enough to work with any GraphRAG-retrieved IoT attack context.
`retrieval_type` is one of: `"cypher"`, `"vector"`, `"combined"`.

#### `generate_comparison_report()`

```python
def generate_comparison_report(
    results: List[ModelComparisonResult],
    output_dir: str = "data/eval",
) -> Dict:
    """
    Aggregate ModelComparisonResult list into a comparison report.

    Computes per-model:
      - mean_latency_ms
      - median_latency_ms
      - mean_grounding_ratio
      - mean_output_tokens
      - error_rate (fraction of responses with error != None)

    Saves:
      - {output_dir}/comparison_report.json
      - {output_dir}/comparison_report.md

    Returns the report dict.
    """
```

Report JSON structure:

```json
{
  "generated_at": "ISO timestamp",
  "query_count": 20,
  "models": {
    "gemini-1.5-flash": {
      "deployment": "cloud",
      "mean_latency_ms": 412.3,
      "median_latency_ms": 380.1,
      "mean_grounding_ratio": 0.82,
      "mean_output_tokens": 143,
      "error_rate": 0.0
    },
    "phi3:latest": { ... },
    "gemma4:e2b": { ... }
  },
  "per_query": [
    {
      "query_id": "te-01",
      "category": "threat_explanation",
      "responses": {
        "gemini-1.5-flash": {
          "latency_ms": 412.3,
          "grounding_ratio": 0.9,
          "output_tokens": 143,
          "response_text": "..."
        }
      }
    }
  ]
}
```

Markdown report: a human-readable table showing per-model stats + per-query grounding ratios.

### Tests (`tests/unit/test_comparison_report.py`)

```python
def make_results(n=3) -> List[ModelComparisonResult]:
    """Helper: creates n synthetic ModelComparisonResult objects."""

def test_generate_comparison_report_structure(tmp_path):
    results = make_results(3)
    report = generate_comparison_report(results, str(tmp_path))
    assert "models" in report
    assert "per_query" in report
    assert len(report["per_query"]) == 3

def test_generate_comparison_report_files_created(tmp_path):
    results = make_results(2)
    generate_comparison_report(results, str(tmp_path))
    assert (tmp_path / "comparison_report.json").exists()
    assert (tmp_path / "comparison_report.md").exists()

def test_generate_comparison_report_aggregates_correctly(tmp_path):
    # two results, same model, latencies 100ms and 200ms
    # assert mean_latency == 150.0
    ...

def test_generate_comparison_report_empty(tmp_path):
    report = generate_comparison_report([], str(tmp_path))
    assert report["query_count"] == 0
    assert report["models"] == {}
```

4 tests total. TDD required.

---

## Progress Ledger

Location: `d:/anil sir/.superpowers/sdd/llm-comparison-progress.md`

---

## Acceptance Criteria

- `python -m pytest tests/unit/test_llm_adapters.py tests/unit/test_llm_comparison.py tests/unit/test_comparison_report.py -v` — all pass
- `python scripts/run_comparison.py --help` exits 0
- `python scripts/run_comparison.py --skip-gemini --benchmark data/eval/comparison_benchmark.json --retrieval-cache data/eval/retrieval_cache.json` either runs successfully or prints a clear error if retrieval cache doesn't exist yet
- No real API calls in the test suite
- `GOOGLE_API_KEY` never hardcoded
