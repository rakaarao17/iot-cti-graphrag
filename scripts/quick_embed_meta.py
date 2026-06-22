import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv() # Force reload .env so it picks up the API key

from config.settings import logger, GOOGLE_API_KEY
from src.services.graph_embeddings.embeddings import embed_attack_type_nodes, embed_mitre_nodes

def quick_embed_meta_nodes():
    logger.info(f"API Key found: {'Yes' if GOOGLE_API_KEY else 'No'}")
    embed_attack_type_nodes()
    embed_mitre_nodes()
    logger.info("Meta node real embeddings complete!")

if __name__ == "__main__":
    quick_embed_meta_nodes()
