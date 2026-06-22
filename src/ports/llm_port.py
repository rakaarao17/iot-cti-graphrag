"""
LLM Port -- Abstract interface for Large Language Models.

Allows swapping between Ollama, OpenAI, local Gemma, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class LLMPort(ABC):
    """
    Abstract LLM service.
    
    Any concrete LLM implementation must inherit from this
    and implement all abstract methods.
    """
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate text given a prompt.
        
        Args:
            prompt: User-facing prompt
            temperature: Creativity (0.0-1.0)
            max_tokens: Max output length
            system_prompt: Optional system context
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If generation failed
        """
        pass
    
    @abstractmethod
    def generate_advanced(self, prompt: str) -> str:
        """
        Advanced generation (e.g., with special parameters).
        
        For some implementations, this may be identical to generate().
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier (e.g., 'gemma-4', 'gpt-4')."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, any]:
        """Return usage statistics (e.g., requests sent, tokens used)."""
        pass
