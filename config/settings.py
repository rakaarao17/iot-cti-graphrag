"""
Centralized configuration for the GraphRAG IoT Cyber Threat Intelligence Pipeline.
Loads settings from .env file and provides defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Project Root ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Load .env ───────────────────────────────────────────────────────────────
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Try .env.example as fallback for reference
    _env_example = PROJECT_ROOT / ".env.example"
    if _env_example.exists():
        load_dotenv(_env_example)

# ── Neo4j ───────────────────────────────────────────────────────────────────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "iot")

# ── Local Ollama ────────────────────────────────────────────────────────────# Local Ollama Settings
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # Embedding dimension (all-MiniLM-L6-v2 output size)

# ── Data Paths ──────────────────────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = Path(os.getenv("DATA_RAW_DIR", str(DATA_DIR / "raw")))
DATA_PROCESSED_DIR = Path(os.getenv("DATA_PROCESSED_DIR", str(DATA_DIR / "processed")))
DATA_SAMPLES_DIR = Path(os.getenv("DATA_SAMPLES_DIR", str(DATA_DIR / "samples")))

# Ensure data directories exist
for _d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_SAMPLES_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Dataset Sources ─────────────────────────────────────────────────────────
IOT23_ZENODO_URL = "https://zenodo.org/records/4743746"
IOT23_LIGHT_URL = "https://mcfp.felk.cvut.cz/publicDatasets/IoT-23-Dataset/IndividualScenarios/"
CICIOT_UNB_URL = "https://www.unb.ca/cic/datasets/iotdataset-2023.html"

# ── Pipeline Parameters ────────────────────────────────────────────────────
# Sampling
DEFAULT_SAMPLE_SIZE = 50_000  # rows per dataset for dev/testing
STRATIFIED_SAMPLE = True      # preserve attack-type distribution

# Neo4j batch ingestion
NEO4J_BATCH_SIZE = 5_000      # flows per transaction
NEO4J_MAX_RETRIES = 3

# Embedding
EMBEDDING_BATCH_SIZE = 100    # texts per Gemini API call
NODE2VEC_DIMENSIONS = 64      # structural embedding dimensions
NODE2VEC_WALK_LENGTH = 30
NODE2VEC_NUM_WALKS = 200
NODE2VEC_WORKERS = 4
NODE2VEC_WINDOW = 10
NODE2VEC_P = 1.0
NODE2VEC_Q = 1.0

# GraphRAG retrieval
TOP_K_RESULTS = 10            # number of vector search results
GRAPH_TRAVERSAL_DEPTH = 2     # hops from retrieved nodes

# LLM
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 4096

# ── Logging ─────────────────────────────────────────────────────────────────
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger("iot_cti_pipeline")


def print_config():
    """Print current configuration for verification."""
    print("=" * 70)
    print("  GraphRAG IoT CTI Pipeline — Configuration")
    print("=" * 70)
    print(f"  Project Root:      {PROJECT_ROOT}")
    print(f"  Neo4j URI:         {NEO4J_URI}")
    print(f"  Neo4j User:        {NEO4J_USER}")
    print(f"  Ollama Endpoint:   {OLLAMA_ENDPOINT}")
    print(f"  Ollama Model:      {OLLAMA_MODEL}")
    print(f"  Embedding Model:   {SENTENCE_TRANSFORMER_MODEL}")
    print(f"  Data Raw Dir:      {DATA_RAW_DIR}")
    print(f"  Data Processed:    {DATA_PROCESSED_DIR}")
    print(f"  Data Samples:      {DATA_SAMPLES_DIR}")
    print(f"  Sample Size:       {DEFAULT_SAMPLE_SIZE:,}")
    print(f"  Neo4j Batch Size:  {NEO4J_BATCH_SIZE:,}")
    print("=" * 70)


if __name__ == "__main__":
    print_config()
