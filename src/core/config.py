"""
Config validator -- Boots system with validated configuration.

Ensures all required environment variables are present and valid
before the application starts.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from src.core.exceptions import ConfigError


class Config:
    """
    Centralized, validated configuration.
    
    Replaces scattered os.getenv() calls with a single,
    validated config object loaded at boot.
    """
    
    # Required fields
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    NEO4J_DATABASE: str
    NEO4J_POOL_SIZE: int
    NEO4J_MAX_RETRIES: int
    
    # Optional with defaults
    GOOGLE_API_KEY: Optional[str]
    OLLAMA_API_URL: str  # New: for adapter compatibility
    OLLAMA_ENDPOINT: str  # Old: maintained for backward compatibility
    OLLAMA_MODEL: str
    
    # Embedding config
    EMBEDDINGS_MODEL: str
    EMBEDDING_DIMENSION: int
    EMBEDDING_BATCH_SIZE: int
    
    # LLM parameters
    LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    LLM_TIMEOUT_SECONDS: int
    
    # Paths
    DATA_RAW_DIR: Path
    DATA_PROCESSED_DIR: Path
    DATA_SAMPLES_DIR: Path
    
    # Logging
    LOG_LEVEL: str
    
    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize config from environment.
        
        Args:
            env_file: Path to .env file. If None, uses default (.env or .env.example)
        """
        self._load_env(env_file)
        self._validate()
        self._setup_paths()
    
    def _load_env(self, env_file: Optional[Path]):
        """Load environment variables from .env file."""
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            # Try default locations
            root = Path(__file__).resolve().parent.parent.parent
            env_path = root / ".env"
            example_path = root / ".env.example"
            
            if env_path.exists():
                load_dotenv(env_path)
            elif example_path.exists():
                load_dotenv(example_path)
    
    def _validate(self):
        """Validate all required fields are present."""
        errors: Dict[str, str] = {}
        
        # Core fields (sensible local defaults so import never crashes; override via .env)
        self.NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687").strip()
        if not self.NEO4J_URI:
            errors["NEO4J_URI"] = "Required environment variable missing"

        self.NEO4J_USER = os.getenv("NEO4J_USER", "neo4j").strip()
        if not self.NEO4J_USER:
            errors["NEO4J_USER"] = "Required environment variable missing"

        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password").strip()
        if not self.NEO4J_PASSWORD:
            errors["NEO4J_PASSWORD"] = "Required environment variable missing"

        self.NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "iot").strip()
        self.NEO4J_POOL_SIZE = int(os.getenv("NEO4J_POOL_SIZE", "20"))
        self.NEO4J_MAX_RETRIES = int(os.getenv("NEO4J_MAX_RETRIES", "3"))
        
        # API keys (Google Gemini)
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip() or None
        
        # Optional with defaults - Ollama
        # Support both OLLAMA_API_URL (new adapter) and OLLAMA_ENDPOINT (old)
        self.OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api")
        self.OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
        # Defaults below match the values the evaluation pipeline actually ran with
        # (previously only in config/settings.py) -- see ADR-0007.
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

        # Embedding configuration (local sentence-transformers; no API key)
        self.EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
        self.EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        self.EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))

        # LLM parameters (match the evaluated pipeline)
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        self.LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "300"))
        
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        if errors:
            error_msg = "; ".join(f"{k}: {v}" for k, v in errors.items())
            raise ConfigError(
                message=f"Configuration validation failed: {error_msg}",
                details=errors,
                recovery_hint="Check .env file and ensure all required variables are set. See .env.example for reference.",
            )
    
    def _setup_paths(self):
        """Create data directories if they don't exist."""
        root = Path(__file__).resolve().parent.parent.parent
        
        self.DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", str(root / "data" / "raw")))
        self.DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", str(root / "data" / "processed")))
        self.DATA_SAMPLES_DIR = Path(os.getenv("DATA_SAMPLES_DIR", str(root / "data" / "samples")))
        
        for d in [self.DATA_RAW_DIR, self.DATA_PROCESSED_DIR, self.DATA_SAMPLES_DIR]:
            d.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return config as dictionary (excluding secrets)."""
        return {
            "neo4j": {
                "uri": self.NEO4J_URI,
                "user": self.NEO4J_USER,
                "database": self.NEO4J_DATABASE,
                # password omitted for safety
            },
            "llm": {
                "ollama_endpoint": self.OLLAMA_ENDPOINT,
                "ollama_model": self.OLLAMA_MODEL,
                "has_google_api_key": bool(self.GOOGLE_API_KEY),
            },
            "paths": {
                "data_raw": str(self.DATA_RAW_DIR),
                "data_processed": str(self.DATA_PROCESSED_DIR),
                "data_samples": str(self.DATA_SAMPLES_DIR),
            },
            "logging": {
                "level": self.LOG_LEVEL,
            },
        }


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def init_config(env_file: Optional[Path] = None) -> Config:
    """Initialize config at boot."""
    global _config
    _config = Config(env_file)
    return _config
