"""
Stage 5: GraphRAG Retrievers.

Implements retrieval strategies that combine vector similarity search
with graph traversal for context-rich information retrieval.

Two retriever types:
1. VectorGraphRetriever " Semantic search + graph neighborhood
2. CypherRetriever " Natural language to Cypher query conversion
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    TOP_K_RESULTS, GRAPH_TRAVERSAL_DEPTH, logger
)
from src.services.knowledge_graph.neo4j_connection import run_query
from src.services.graph_embeddings.embeddings import get_local_embeddings
from src.services.graphrag.vector_store import vector_search_with_traversal


class VectorGraphRetriever:
    """
    Retriever that combines vector similarity search with graph traversal.

    1. Converts the query to an embedding using local sentence-transformers
    2. Finds semantically similar nodes via Neo4j vector index
    3. Traverses graph neighbors for additional context
    4. Formats the retrieved information as structured context
    """

    def __init__(
        self,
        top_k: int = None,
        traversal_depth: int = None,
    ):
        self.top_k = top_k or TOP_K_RESULTS
        self.traversal_depth = traversal_depth or GRAPH_TRAVERSAL_DEPTH

    def retrieve(self, query: str, search_type: str = "device") -> Dict:
        """
        Retrieve relevant context from the knowledge graph.

        Args:
            query: Natural language question
            search_type: "device", "attack", or "mitre"

        Returns:
            Dict with 'results', 'context_text', and 'metadata'
        """
        # Step 1: Embed the query
        embeddings = get_local_embeddings([query])
        if not embeddings:
            return {"results": [], "context_text": "No embedding generated", "metadata": {}}

        query_embedding = embeddings[0]

        # Step 2: Determine which index to search
        index_map = {
            "device": "device_embedding",
            "attack": "attack_embedding",
            "mitre": "mitre_embedding",
        }
        index_name = index_map.get(search_type, "device_embedding")

        # Step 3: Vector search with graph traversal
        results = vector_search_with_traversal(
            query_embedding=query_embedding,
            index_name=index_name,
            top_k=self.top_k,
            traversal_depth=self.traversal_depth,
        )

        # Step 4: Format as context text for LLM
        context_text = self._format_context(results, search_type)

        return {
            "results": results,
            "context_text": context_text,
            "metadata": {
                "query": query,
                "search_type": search_type,
                "index": index_name,
                "result_count": len(results),
            },
        }

    def _format_context(self, results: List[Dict], search_type: str) -> str:
        """Format retrieval results as structured text for the LLM."""
        if not results:
            return "No relevant results found in the knowledge graph."

        lines = [f"=== Knowledge Graph Context ({len(results)} results) ===\n"]

        if search_type == "device":
            for i, r in enumerate(results, 1):
                lines.append(f"--- Device {i} (relevance: {r.get('score', 0):.3f}) ---")
                lines.append(f"  IP: {r.get('ip', 'N/A')}")
                lines.append(f"  Role: {r.get('role', 'N/A')}")
                lines.append(f"  Dataset: {r.get('dataset', 'N/A')}")
                mal_ratio = r.get('malicious_ratio')
                mal_ratio = mal_ratio if mal_ratio is not None else 0
                lines.append(f"  Malicious Ratio: {mal_ratio:.1%}")
                lines.append(f"  Malicious Flows: {r.get('malicious_flows', 0):,}")

                attacks = r.get('attacks', [])
                if attacks:
                    lines.append(f"  Attack Types: {', '.join(attacks)}")

                mitre = r.get('mitre_ids', [])
                mitre_names = r.get('mitre_names', [])
                if mitre:
                    mapping = [f"{mid} ({mname})" for mid, mname in zip(mitre, mitre_names)]
                    lines.append(f"  MITRE ATT&CK: {', '.join(mapping)}")

                peers = r.get('top_peers', [])
                if peers:
                    lines.append(f"  Communicates with: {', '.join(peers)}")

                desc = r.get('description', '')
                if desc:
                    lines.append(f"  Profile: {desc[:200]}")
                lines.append("")

        elif search_type == "attack":
            for i, r in enumerate(results, 1):
                lines.append(f"--- Attack {i} (relevance: {r.get('score', 0):.3f}) ---")
                lines.append(f"  Name: {r.get('name', 'N/A')}")
                lines.append(f"  Category: {r.get('category', 'N/A')}")
                lines.append(f"  Severity: {r.get('severity', 'N/A')}")
                lines.append(f"  Total Flows: {r.get('flow_count', 0):,}")

                if r.get('mitre_id'):
                    lines.append(f"  MITRE: {r['mitre_id']} ({r.get('mitre_technique', '')})")
                    lines.append(f"  Tactic: {r.get('mitre_tactic', '')}")

                desc = r.get('description', '')
                if desc:
                    lines.append(f"  Description: {desc[:300]}")
                lines.append("")

        elif search_type == "mitre":
            for i, r in enumerate(results, 1):
                node = r.get("node", r)
                lines.append(f"--- MITRE Technique {i} ---")
                for key, value in node.items():
                    if key not in ("embedding",):
                        lines.append(f"  {key}: {value}")
                lines.append("")

        return "\n".join(lines)

    def multi_search(self, query: str) -> Dict:
        """
        Search across all index types and combine results.
        Useful for broad investigative queries.
        """
        all_results = {}
        all_context = []

        for search_type in ["device", "attack", "mitre"]:
            result = self.retrieve(query, search_type=search_type)
            all_results[search_type] = result["results"]
            if result["results"]:
                all_context.append(f"\n{'='*60}")
                all_context.append(f"  {search_type.upper()} SEARCH RESULTS")
                all_context.append(f"{'='*60}")
                all_context.append(result["context_text"])

        return {
            "results": all_results,
            "context_text": "\n".join(all_context),
            "metadata": {"query": query, "search_types": list(all_results.keys())},
        }


class CypherRetriever:
    """
    Retriever that converts natural language to Cypher queries.

    Uses a set of pre-built query templates matched by keyword analysis.
    For production, this could be replaced with LLM-based Cypher generation.
    """

    QUERY_TEMPLATES = {
        "top_attackers": {
            "keywords": ["top", "most", "attacker", "malicious", "dangerous", "threat"],
            "query": """
                MATCH (d:Device)-[:INITIATES]->(f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
                WHERE a.name <> 'Benign'
                WITH d, count(f) as malicious_flows,
                     collect(DISTINCT a.name) as attacks
                RETURN d.ip as ip, malicious_flows, attacks
                ORDER BY malicious_flows DESC LIMIT 10
            """,
            "description": "Top 10 most malicious devices by flow count",
        },
        "attack_types": {
            "keywords": ["attack", "type", "category", "classification", "kind"],
            "query": """
                MATCH (a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
                MATCH (a)-[:BELONGS_TO]->(c:AttackCategory)
                WITH a.name as attack, c.name as category,
                     count(f) as count, c.severity as severity
                RETURN attack, category, severity, count
                ORDER BY count DESC LIMIT 20
            """,
            "description": "All attack types with flow counts and categories",
        },
        "mitre_mapping": {
            "keywords": ["mitre", "att&ck", "technique", "tactic", "framework"],
            "query": """
                MATCH (m:MITRETechnique)<-[:MAPS_TO]-(a:AttackType)<-[:CLASSIFIED_AS]-(f:Flow)
                WITH m, collect(DISTINCT a.name) as attacks, count(f) as flows
                RETURN m.technique_id as id, m.name as technique,
                       m.tactic as tactic, attacks, flows
                ORDER BY flows DESC
            """,
            "description": "MITRE ATT&CK technique coverage with attack mappings",
        },
        "device_profile": {
            "keywords": ["device", "ip", "profile", "behavior", "activity"],
            "query": """
                MATCH (d:Device)
                WHERE d.total_degree IS NOT NULL
                RETURN d.ip as ip, d.role as role,
                       d.malicious_ratio as mal_ratio,
                       d.total_degree as degree,
                       d.attack_diversity as attack_types
                ORDER BY d.malicious_ratio DESC LIMIT 20
            """,
            "description": "Device profiles sorted by malicious activity",
        },
        "dataset_comparison": {
            "keywords": ["compare", "comparison", "dataset", "iot-23", "ciciot", "difference"],
            "query": """
                MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)-[:BELONGS_TO]->(c:AttackCategory)
                WITH f.dataset as dataset, c.name as category, count(f) as count
                RETURN dataset, category, count
                ORDER BY dataset, count DESC
            """,
            "description": "Attack distribution comparison between datasets",
        },
        "network_summary": {
            "keywords": ["summary", "overview", "statistics", "total", "count", "how many"],
            "query": """
                MATCH (d:Device) WITH count(d) as devices
                MATCH (f:Flow) WITH devices, count(f) as flows
                MATCH (a:AttackType) WITH devices, flows, count(a) as attack_types
                MATCH (m:MITRETechnique) WITH devices, flows, attack_types, count(m) as mitre
                RETURN devices, flows, attack_types, mitre
            """,
            "description": "High-level network summary statistics",
        },
    }

    def retrieve(self, query: str) -> Dict:
        """
        Match the query to a Cypher template and execute it.

        Args:
            query: Natural language question

        Returns:
            Dict with results and context text
        """
        query_lower = query.lower()

        # Score each template by keyword matches
        best_template = None
        best_score = 0

        for name, template in self.QUERY_TEMPLATES.items():
            score = sum(1 for kw in template["keywords"] if kw in query_lower)
            if score > best_score:
                best_score = score
                best_template = (name, template)

        if not best_template or best_score == 0:
            # Default to network summary
            best_template = ("network_summary", self.QUERY_TEMPLATES["network_summary"])

        name, template = best_template
        logger.info(f"Matched query to template: {name} (score: {best_score})")

        results = run_query(template["query"])

        # Format context
        context_lines = [
            f"=== Cypher Query Results: {template['description']} ===\n",
            f"Query Template: {name}",
            f"Results: {len(results)} records\n",
        ]

        for i, r in enumerate(results, 1):
            context_lines.append(f"  Record {i}:")
            for key, value in r.items():
                context_lines.append(f"    {key}: {value}")
            context_lines.append("")

        return {
            "results": results,
            "context_text": "\n".join(context_lines),
            "metadata": {
                "query": query,
                "template": name,
                "description": template["description"],
                "match_score": best_score,
            },
        }


# "" Convenience Functions """""""""""""""""""""""""""""""""""""""""""""""""""

def retrieve_context(query: str, method: str = "auto") -> Dict:
    """
    High-level retrieval function that picks the best strategy.

    Args:
        query: Natural language question
        method: "vector", "cypher", "multi", or "auto"
    """
    if method == "vector":
        retriever = VectorGraphRetriever()
        return retriever.retrieve(query)
    elif method == "cypher":
        retriever = CypherRetriever()
        return retriever.retrieve(query)
    elif method == "multi":
        retriever = VectorGraphRetriever()
        return retriever.multi_search(query)
    else:  # auto
        # Use Cypher for structured questions, vector for semantic
        structured_keywords = ["how many", "total", "count", "list", "top", "compare"]
        if any(kw in query.lower() for kw in structured_keywords):
            retriever = CypherRetriever()
            return retriever.retrieve(query)
        else:
            retriever = VectorGraphRetriever()
            return retriever.retrieve(query)


if __name__ == "__main__":
    # Demo retrieval
    test_queries = [
        "What are the most dangerous IoT devices?",
        "How many attacks are in the dataset?",
        "Show me MITRE ATT&CK technique coverage",
    ]

    for q in test_queries:
        print(f"\n{'-' * 60}")
        print(f"  Query: {q}")
        print(f"{'-' * 60}")
        result = retrieve_context(q)
        print(result["context_text"][:500])
