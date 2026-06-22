"""
Ollama Adapter -- Implements LLMPort for local Ollama service.

Wraps the Ollama HTTP API with proper error handling and retry logic.
"""

import time
import requests
from typing import Dict, Optional, Any

from src.ports.llm_port import LLMPort
from src.core.exceptions import LLMError


class OllamaAdapter(LLMPort):
    """
    Local Ollama LLM adapter.
    
    Connects to Ollama via HTTP and generates text for cybersecurity analysis.
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
        model: str = "gemma4:e2b",
        endpoint: str = "http://localhost:11434/api/generate",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ):
        self.model = model
        self.endpoint = endpoint
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.request_count = 0
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate text from Ollama."""
        target_temp = temperature if temperature is not None else self.temperature
        target_tokens = max_tokens or self.max_tokens
        target_system = system_prompt or self.system_prompt
        
        full_prompt = f"{target_system}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": target_temp,
                "num_predict": target_tokens,
            },
        }
        
        for attempt in range(3):
            try:
                response = requests.post(self.endpoint, json=payload, timeout=None)
                response.raise_for_status()
                
                self.request_count += 1
                result = response.json()
                
                if "response" in result:
                    return result["response"]
                else:
                    raise LLMError(
                        message="Unexpected response format from Ollama",
                        details={"response": result},
                        recovery_hint="Check Ollama service status and model availability.",
                    )
            
            except requests.exceptions.RequestException as e:
                wait = 2 ** attempt
                if attempt < 2:
                    time.sleep(wait)
                    continue
                raise LLMError(
                    message=f"Failed to connect to Ollama after 3 attempts",
                    details={"endpoint": self.endpoint, "error": str(e)},
                    recovery_hint="Ensure Ollama is running and accessible at the configured endpoint.",
                )
            except Exception as e:
                raise LLMError(
                    message=f"Ollama generation failed: {e}",
                    details={"error": str(e)},
                )
        
        raise LLMError(message="Ollama generation failed after retries")
    
    def generate_advanced(self, prompt: str) -> str:
        """For local Ollama, same as generate()."""
        return self.generate(prompt)
    
    def get_model_name(self) -> str:
        return self.model
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "endpoint": self.endpoint,
            "requests_sent": self.request_count,
        }
