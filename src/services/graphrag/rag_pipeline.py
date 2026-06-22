"""
Stage 5: GraphRAG Pipeline Orchestration.

Combines retrieval (vector + graph) with LLM generation
to answer natural language questions about IoT cyber threats.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import logger
from src.services.graphrag.retrievers import VectorGraphRetriever, CypherRetriever, retrieve_context


class GraphRAGPipeline:
    """
    End-to-end GraphRAG pipeline for IoT Cyber Threat Intelligence.

    Flow:
    1. User asks a natural language question
    2. Retrieve relevant subgraph context via vector + Cypher
    3. Format context as a structured prompt
    4. Send to LLM for analysis and explanation
    5. Return generated answer with evidence
    """

    def __init__(self, llm_client=None):
        """
        Initialize the GraphRAG pipeline.

        Args:
            llm_client: A Gemini LLM client instance.
                        If None, will be created from stage6.
        """
        self.vector_retriever = VectorGraphRetriever()
        self.cypher_retriever = CypherRetriever()
        self.llm_client = llm_client

    def _get_llm(self):
        """Lazy-load the LLM client."""
        if self.llm_client is None:
            try:
                from src.services.threat_explanation.ollama_client import OllamaClient
                self.llm_client = OllamaClient()
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                return None
        return self.llm_client

    def query(
        self,
        question: str,
        retrieval_method: str = "auto",
        search_type: str = "device",
        include_evidence: bool = True,
    ) -> Dict:
        """
        Process a natural language question through the GraphRAG pipeline.

        Args:
            question: User's natural language question
            retrieval_method: "vector", "cypher", "multi", or "auto"
            search_type: "device", "attack", or "mitre" (for vector search)
            include_evidence: Whether to include raw evidence in output

        Returns:
            Dict with 'answer', 'evidence', 'metadata'
        """
        logger.info(f"GraphRAG Query: {question}")

        # Step 1: Retrieve context
        if retrieval_method == "multi":
            retrieval = self.vector_retriever.multi_search(question)
        elif retrieval_method == "cypher":
            retrieval = self.cypher_retriever.retrieve(question)
        elif retrieval_method == "vector":
            retrieval = self.vector_retriever.retrieve(question, search_type=search_type)
        else:
            retrieval = retrieve_context(question)

        context_text = retrieval.get("context_text", "No context available")
        logger.info(f"Retrieved {len(retrieval.get('results', []))} context items")

        # Step 2: Generate LLM response
        llm = self._get_llm()
        if llm is None:
            return {
                "answer": f"LLM not available. Here is the raw context:\n\n{context_text}",
                "evidence": retrieval.get("results", []),
                "metadata": retrieval.get("metadata", {}),
            }

        # Build the prompt
        prompt = self._build_prompt(question, context_text)

        # Generate answer
        try:
            answer = llm.generate(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = f"Error generating response: {e}\n\nRaw context:\n{context_text}"

        result = {
            "answer": answer,
            "metadata": {
                **retrieval.get("metadata", {}),
                "retrieval_method": retrieval_method,
            },
        }

        if include_evidence:
            result["evidence"] = retrieval.get("results", [])

        return result

    def _build_prompt(self, question: str, context: str) -> str:
        """Build the LLM prompt combining the question with retrieved context."""
        return f"""You are an expert IoT cybersecurity analyst with deep knowledge of network threats, MITRE ATT&CK framework, and IoT malware families.

You are analyzing data from a Knowledge Graph built from the IoT-23 and CICIoT2023 datasets, which contain real-world IoT network traffic including both benign traffic and various cyber attacks.

## Retrieved Knowledge Graph Context

{context}

## User Question

{question}

## Instructions

Based on the knowledge graph context provided above, give a thorough, expert-level answer to the user's question. Your response should:

1. **Directly answer the question** with specific data from the context
2. **Provide technical analysis** of the attack patterns, devices, or techniques involved
3. **Reference MITRE ATT&CK techniques** when relevant
4. **Assess severity and risk** based on the evidence
5. **Recommend mitigations** or defensive actions when appropriate
6. **Cite specific data points** (IPs, flow counts, attack types) from the context

Format your response with clear sections and bullet points for readability.
If the context doesn't contain sufficient information to answer the question, say so clearly and suggest what additional data or queries might help.
"""

    def investigate(self, topic: str) -> Dict:
        """
        Run a comprehensive investigation using all retrieval methods.
        Combines vector search, Cypher queries, and multi-type search.
        """
        logger.info(f"Running comprehensive investigation: {topic}")

        # Get context from all methods
        multi_result = self.vector_retriever.multi_search(topic)
        cypher_result = self.cypher_retriever.retrieve(topic)

        combined_context = (
            f"=== SEMANTIC SEARCH RESULTS ===\n"
            f"{multi_result.get('context_text', '')}\n\n"
            f"=== STRUCTURED QUERY RESULTS ===\n"
            f"{cypher_result.get('context_text', '')}"
        )

        # Generate comprehensive analysis
        llm = self._get_llm()
        if llm:
            prompt = f"""You are an expert IoT cybersecurity analyst conducting a comprehensive investigation.

## Investigation Topic: {topic}

## Evidence from Knowledge Graph

{combined_context}

## Investigation Report

Produce a detailed investigation report covering:
1. **Executive Summary** " Key findings in 2-3 sentences
2. **Threat Assessment** " Severity, scope, and impact analysis
3. **Technical Details** " Specific IPs, attack types, flow patterns
4. **MITRE ATT&CK Mapping** " Relevant techniques and tactics
5. **Timeline Analysis** " Temporal patterns if available
6. **Recommendations** " Immediate actions and long-term mitigations
7. **Intelligence Gaps** " What additional data would improve the analysis

Be specific, cite data points, and provide actionable intelligence.
"""
            answer = llm.generate(prompt)
        else:
            answer = f"Investigation context (LLM unavailable):\n\n{combined_context}"

        return {
            "answer": answer,
            "evidence": {
                "semantic": multi_result.get("results", {}),
                "structured": cypher_result.get("results", []),
            },
            "metadata": {"topic": topic, "method": "comprehensive_investigation"},
        }


# "" Convenience Function """"""""""""""""""""""""""""""""""""""""""""""""""""

def ask(question: str, method: str = "auto") -> str:
    """
    Simple interface for asking questions about the IoT threat landscape.

    Args:
        question: Natural language question
        method: Retrieval method

    Returns:
        Answer string
    """
    pipeline = GraphRAGPipeline()
    result = pipeline.query(question, retrieval_method=method)
    return result["answer"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GraphRAG Query Interface")
    parser.add_argument("question", nargs="?", default="What are the main threats in this IoT network?")
    parser.add_argument("--method", choices=["auto", "vector", "cypher", "multi"], default="auto")
    args = parser.parse_args()

    result = ask(args.question, method=args.method)
    print(f"\n{'-' * 70}")
    print(f"  Question: {args.question}")
    print(f"{'-' * 70}")
    print(result)
