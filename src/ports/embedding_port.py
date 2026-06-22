"""
Embedding Port -- Abstract interface for embedding services.

Allows swapping between Gemini, OpenAI, local models, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EmbeddingPort(ABC):
    """
    Abstract embedding service.
    
    Implementations convert text to vectors.
    """
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding vector (list of floats)
            
        Raises:
            EmbeddingError: If embedding failed
        """
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Return vector dimensionality (e.g., 768 for Gemini)."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return model identifier."""
        pass
