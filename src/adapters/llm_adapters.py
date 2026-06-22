"""
Unified LLM adapter interface for local Ollama models only.
Supports: gemma4:e2b, phi3:latest, zeroday-phi3-ciciot-v2:latest

All adapters share:
- temperature = 0.0
- max_output_tokens = 512
- Token counts are estimates: character count // 4
"""

import sys
import time
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

import requests


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class LLMAdapter(Protocol):
    model_name: str   # e.g. "gemma4:e2b", "phi3:latest", "zeroday-phi3-ciciot-v2:latest"
    deployment: str   # "local"

    def generate(self, prompt: str, context: str) -> "LLMResponse":
        ...


# ---------------------------------------------------------------------------
# Response dataclass
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_prompt(prompt: str, context: str) -> str:
    return (
        "You are a cybersecurity analyst. Use ONLY the provided context to answer.\n"
        "Do not use knowledge outside the context. If the context is insufficient, say so.\n\n"
        f"### Context\n{context}\n\n"
        f"### Question\n{prompt}\n\n"
        "### Answer"
    )


# ---------------------------------------------------------------------------
# OllamaAdapter -- local, talks to Ollama REST API
# ---------------------------------------------------------------------------

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
            print(f"[WARN] {self.model_name}: {e}", file=sys.stderr)
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
