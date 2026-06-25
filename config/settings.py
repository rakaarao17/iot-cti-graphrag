"""Pipeline settings for the GraphRAG IoT Cyber Threat Intelligence Pipeline.

Single source of truth: all values shared with the adapter/test layer are pulled
from the canonical `src.core.config.Config` (see ADR-0007). Pipeline-only
constants that the hexagonal core does not need (node2vec params, dataset URLs,
sampling, logger) are defined here. Existing `from config.settings import X`
imports keep working unchanged.
"""

import logging
from pathlib import Path

from src.core.config import get_config

# Canonical, validated config (loads .env / .env.example once).
_c = get_config()

# ---------------------------------------------------------------------------
# Shared values (canonical source = src.core.config.Config)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

NEO4J_URI = _c.NEO4J_URI
NEO4J_USER = _c.NEO4J_USER
NEO4J_PASSWORD = _c.NEO4J_PASSWORD
NEO4J_DATABASE = _c.NEO4J_DATABASE
NEO4J_MAX_RETRIES = _c.NEO4J_MAX_RETRIES

OLLAMA_ENDPOINT = _c.OLLAMA_ENDPOINT
OLLAMA_MODEL = _c.OLLAMA_MODEL

EMBEDDING_DIMENSION = _c.EMBEDDING_DIMENSION
EMBEDDING_BATCH_SIZE = _c.EMBEDDING_BATCH_SIZE

LLM_TEMPERATURE = _c.LLM_TEMPERATURE
LLM_MAX_TOKENS = _c.LLM_MAX_TOKENS

DATA_RAW_DIR = _c.DATA_RAW_DIR
DATA_PROCESSED_DIR = _c.DATA_PROCESSED_DIR
DATA_SAMPLES_DIR = _c.DATA_SAMPLES_DIR
DATA_DIR = PROJECT_ROOT / "data"

LOG_LEVEL = _c.LOG_LEVEL

# ---------------------------------------------------------------------------
# Pipeline-only constants (not needed by the adapter/core layer)
# ---------------------------------------------------------------------------
SENTENCE_TRANSFORMER_MODEL = _c.EMBEDDINGS_MODEL  # local sentence-transformers model

# Dataset sources
IOT23_ZENODO_URL = "https://zenodo.org/records/4743746"
IOT23_LIGHT_URL = "https://mcfp.felk.cvut.cz/publicDatasets/IoT-23-Dataset/IndividualScenarios/"
CICIOT_UNB_URL = "https://www.unb.ca/cic/datasets/iotdataset-2023.html"

# Sampling
DEFAULT_SAMPLE_SIZE = 50_000   # rows per dataset for dev/testing
STRATIFIED_SAMPLE = True       # preserve attack-type distribution

# Neo4j batch ingestion
NEO4J_BATCH_SIZE = 5_000       # flows per transaction

# node2vec structural embeddings
NODE2VEC_DIMENSIONS = 64
NODE2VEC_WALK_LENGTH = 30
NODE2VEC_NUM_WALKS = 200
NODE2VEC_WORKERS = 4
NODE2VEC_WINDOW = 10
NODE2VEC_P = 1.0
NODE2VEC_Q = 1.0

# GraphRAG retrieval
TOP_K_RESULTS = 10             # vector search results
GRAPH_TRAVERSAL_DEPTH = 2      # hops from retrieved nodes

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format=LOG_FORMAT)
logger = logging.getLogger("iot_cti_pipeline")


def print_config():
    """Print current configuration for verification."""
    print("=" * 70)
    print("  GraphRAG IoT CTI Pipeline - Configuration")
    print("=" * 70)
    print(f"  Project Root:      {PROJECT_ROOT}")
    print(f"  Neo4j URI:         {NEO4J_URI}")
    print(f"  Neo4j User:        {NEO4J_USER}")
    print(f"  Neo4j Database:    {NEO4J_DATABASE}")
    print(f"  Ollama Endpoint:   {OLLAMA_ENDPOINT}")
    print(f"  Ollama Model:      {OLLAMA_MODEL}")
    print(f"  Embedding Model:   {SENTENCE_TRANSFORMER_MODEL}")
    print(f"  Embedding Dim:     {EMBEDDING_DIMENSION}")
    print(f"  LLM Temperature:   {LLM_TEMPERATURE}")
    print(f"  LLM Max Tokens:    {LLM_MAX_TOKENS}")
    print(f"  Data Raw Dir:      {DATA_RAW_DIR}")
    print(f"  Data Processed:    {DATA_PROCESSED_DIR}")
    print(f"  Data Samples:      {DATA_SAMPLES_DIR}")
    print(f"  Sample Size:       {DEFAULT_SAMPLE_SIZE:,}")
    print(f"  Neo4j Batch Size:  {NEO4J_BATCH_SIZE:,}")
    print("=" * 70)


if __name__ == "__main__":
    print_config()
