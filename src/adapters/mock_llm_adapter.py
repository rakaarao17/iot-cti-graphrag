"""
Mock LLM Adapter -- For testing without Ollama.

Returns deterministic responses suitable for unit tests.
"""

from typing import Dict, Optional, Any

from src.ports.llm_port import LLMPort


class MockLLMAdapter(LLMPort):
    """
    Mock LLM for testing.
    
    Returns predictable responses without calling external services.
    """
    
    def __init__(self):
        self.request_count = 0
        self.last_prompt = None
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Return deterministic response."""
        self.request_count += 1
        self.last_prompt = prompt
        
        # Return mock response based on prompt content
        if "threat" in prompt.lower():
            return (
                "Based on the provided graph context, the device exhibits "
                "moderate threat indicators consistent with DDoS reconnaissance. "
                "Recommended mitigation: Apply rate limiting on port 80."
            )
        elif "device" in prompt.lower():
            return (
                "Device 192.168.1.1 has initiated 1,500 flows, "
                "of which 300 were flagged as anomalous. "
                "Attack types: DDoS-SYN_Flood (200), Port Scan (100)."
            )
        else:
            return "Mock LLM response for testing purposes."
    
    def generate_advanced(self, prompt: str) -> str:
        return self.generate(prompt)
    
    def get_model_name(self) -> str:
        return "mock-llm"
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "model": "mock-llm",
            "requests_sent": self.request_count,
            "last_prompt": self.last_prompt[:50] if self.last_prompt else None,
        }
