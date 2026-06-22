"""
Centralized exception hierarchy for the GraphRAG pipeline.

All exceptions inherit from AppError and are structured to include
context, error codes, and recovery suggestions.
"""

from typing import Optional, Dict, Any
import json


class AppError(Exception):
    """
    Base application error with structured envelope.
    
    All domain exceptions inherit from this.
    """
    
    code: str = "APP_ERROR"
    http_status: int = 500
    message: str = "An unexpected error occurred"
    
    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None,
    ):
        self.message = message or self.message
        self.code = code or self.code
        self.details = details or {}
        self.recovery_hint = recovery_hint
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return structured error envelope."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "recovery_hint": self.recovery_hint,
            }
        }
    
    def to_json(self) -> str:
        """Return JSON-serialized error."""
        return json.dumps(self.to_dict())


class ValidationError(AppError):
    """Configuration or input validation failed."""
    code = "VALIDATION_ERROR"
    http_status = 400
    message = "Validation failed"


class ConfigError(ValidationError):
    """Configuration validation failed (subset of ValidationError)."""
    code = "CONFIG_ERROR"
    message = "Configuration error"


class GraphError(AppError):
    """Neo4j graph operation failed."""
    code = "GRAPH_ERROR"
    http_status = 503
    message = "Graph database error"


class LLMError(AppError):
    """LLM service error (Ollama, Gemini, etc.)."""
    code = "LLM_ERROR"
    http_status = 503
    message = "LLM service error"


class EmbeddingError(AppError):
    """Embedding generation failed."""
    code = "EMBEDDING_ERROR"
    http_status = 503
    message = "Embedding error"


class DataError(AppError):
    """Data processing or format error."""
    code = "DATA_ERROR"
    http_status = 400
    message = "Data processing error"


class NotFoundError(AppError):
    """Resource not found."""
    code = "NOT_FOUND"
    http_status = 404
    message = "Resource not found"


class HallucinationDetectedError(AppError):
    """LLM output failed factuality validation."""
    code = "HALLUCINATION_DETECTED"
    http_status = 422
    message = "LLM output validation failed"


class TimeoutError(AppError):
    """Operation timed out."""
    code = "TIMEOUT"
    http_status = 504
    message = "Operation timeout"
