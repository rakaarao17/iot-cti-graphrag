"""
Stage 6: Ollama LLM Client.

Wrapper around the local Ollama API for generating threat explanations.
Supports multiple local models, primarily Gemma, and tracking.
"""

import sys
import time
import requests
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import LLM_TEMPERATURE, LLM_MAX_TOKENS, OLLAMA_MODEL, OLLAMA_ENDPOINT, logger

class OllamaClient:
    """
    Local Ollama API client for cybersecurity threat analysis.
    """

    DEFAULT_SYSTEM_PROMPT = """You are CyberGuard AI, an expert IoT cybersecurity analyst specializing in:
- Network traffic analysis and intrusion detection
- IoT malware families (Mirai, Torii, Hajime, Okiru, Muhstik)
- MITRE ATT&CK framework for IoT/embedded systems
- DDoS, C&C, reconnaissance, brute force, and spoofing attacks
- Knowledge graphs and graph-based threat intelligence

Always provide specific, actionable analysis with data-backed conclusions.
Reference MITRE ATT&CK technique IDs when discussing attack patterns.
"""

    def __init__(
        self,
        model: str = None,
        endpoint: str = None,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ):
        self.model = model or OLLAMA_MODEL
        self.endpoint = endpoint or OLLAMA_ENDPOINT
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE
        self.max_tokens = max_tokens or LLM_MAX_TOKENS
        self.request_count = 0

    def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_retries: int = 3,
    ) -> str:
        """Generate a response from Ollama."""
        target_model = model or self.model
        target_temp = temperature if temperature is not None else self.temperature

        full_prompt = f"{self.system_prompt}\n\n{prompt}"

        payload = {
            "model": target_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": target_temp,
                "num_predict": self.max_tokens
            }
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(self.endpoint, json=payload, timeout=None)
                response.raise_for_status()
                
                self.request_count += 1
                result = response.json()
                
                if "response" in result:
                    return result["response"]
                else:
                    logger.warning(f"Unexpected response format from Ollama: {result}")
                    
            except requests.exceptions.RequestException as e:
                wait = 2 ** attempt
                logger.warning(f"Ollama connection error: {e}. Is Ollama running? Retrying in {wait}s")
                time.sleep(wait)
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
                
        return "Error: Failed to connect to local Ollama instance after maximum retries. Please ensure Ollama is running."

    def generate_advanced(self, prompt: str) -> str:
        """For local Ollama, we simply use the same generation model for advanced requests."""
        return self.generate(prompt)

    def get_stats(self) -> dict:
        return {
            "model": self.model,
            "requests": self.request_count,
        }

def test_ollama():
    """Test the Ollama client with a simple query."""
    client = OllamaClient()
    print("Testing connection to Ollama...")
    response = client.generate("Briefly explain what a Mirai botnet is and how it affects IoT devices.")
    print(f"\n{'=' * 60}")
    print(f"  Ollama Test Response")
    print(f"{'=' * 60}")
    print(response)
    print(f"\nStats: {client.get_stats()}")

if __name__ == "__main__":
    test_ollama()
