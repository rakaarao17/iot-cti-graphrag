"""
Stage 6: Threat Explainer " End-to-End Interface.

Combines GraphRAG retrieval with LLM generation through curated
prompt templates to provide comprehensive cyber threat analysis.
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import logger
from src.services.graphrag.retrievers import VectorGraphRetriever, CypherRetriever
from src.services.threat_explanation.ollama_client import OllamaClient
from src.services.threat_explanation.prompt_templates import get_template
from src.services.threat_explanation.grounding import check_grounding



class ThreatExplainer:
    """
    Generates human-readable cyber threat explanations using GraphRAG and Local Ollama Models.

    Provides high-level methods for common analysis tasks:
    - Device threat profiling
    - Attack type explanation
    - Incident report generation
    - MITRE ATT&CK mapping
    - Free-form investigation
    """

    def __init__(self, llm_client: OllamaClient = None):
        self.llm = llm_client or OllamaClient()
        self.vector_retriever = VectorGraphRetriever()
        self.cypher_retriever = CypherRetriever()

    def _retrieve_context(self, query: str, search_type: str = "device") -> str:
        """Retrieve context from the knowledge graph."""
        try:
            result = self.vector_retriever.retrieve(query, search_type=search_type)
            return result.get("context_text", "No context available")
        except Exception as e:
            logger.warning(f"Vector retrieval failed: {e}")
            # Fallback to Cypher
            try:
                result = self.cypher_retriever.retrieve(query)
                return result.get("context_text", "No context available")
            except Exception as e2:
                logger.error(f"All retrieval failed: {e2}")
                return "Context retrieval unavailable"

    def explain_device(self, ip_address: str) -> Dict:
        """
        Generate a comprehensive threat profile for a specific device.

        Args:
            ip_address: The IP address of the device to analyze

        Returns:
            Dict with 'analysis', 'threat_level', 'recommendations'
        """
        logger.info(f"Analyzing device: {ip_address}")

        # Get device-specific context from KG
        from src.services.graph_embeddings.cypher_queries import get_device_profile
        device_info = get_device_profile(ip_address)

        if not device_info:
            return {
                "analysis": f"No data found for device {ip_address}",
                "threat_level": "UNKNOWN",
            }

        # Format device context
        device_context = "\n".join(f"  {k}: {v}" for k, v in device_info.items())

        # Get broader graph context
        graph_context = self._retrieve_context(
            f"IoT device at {ip_address} threat analysis",
            search_type="device"
        )

        # Generate analysis
        template = get_template("device_profile")
        prompt = template.format(
            device_context=device_context,
            graph_context=graph_context,
        )

        analysis = self.llm.generate(prompt)

        grounding = check_grounding(analysis, graph_context)
        return {
            "analysis": analysis,
            "device_info": device_info,
            "ip": ip_address,
            "grounding_ratio": grounding.grounding_ratio,
            "ungrounded_entities": grounding.ungrounded_entities,
        }

    def explain_attack(self, attack_type: str) -> Dict:
        """
        Explain an attack type with full MITRE ATT&CK mapping.

        Args:
            attack_type: The attack type name (e.g., "DDoS-TCP_Flood")

        Returns:
            Dict with detailed attack analysis
        """
        logger.info(f"Analyzing attack type: {attack_type}")

        # Get attack-specific context
        from src.services.graph_embeddings.cypher_queries import get_attack_to_mitre_path
        attack_info = get_attack_to_mitre_path(attack_type)

        attack_context = "\n".join(f"  {k}: {v}" for k, v in attack_info.items()) if attack_info else f"Attack type: {attack_type}"

        graph_context = self._retrieve_context(
            f"{attack_type} attack analysis IoT",
            search_type="attack"
        )

        template = get_template("attack_explanation")
        prompt = template.format(
            attack_context=attack_context,
            graph_context=graph_context,
        )

        analysis = self.llm.generate(prompt)

        grounding = check_grounding(analysis, graph_context)
        return {
            "analysis": analysis,
            "attack_info": attack_info,
            "attack_type": attack_type,
            "grounding_ratio": grounding.grounding_ratio,
            "ungrounded_entities": grounding.ungrounded_entities,
        }

    def generate_incident_report(
        self,
        incident_description: str = None,
        classification: str = "MEDIUM",
    ) -> Dict:
        """
        Generate a formal security incident report.

        Args:
            incident_description: Description of the incident
            classification: Severity classification

        Returns:
            Dict with the incident report
        """
        incident_description = incident_description or "IoT network security assessment based on collected traffic data"

        logger.info(f"Generating incident report: {incident_description[:50]}...")

        # Get comprehensive context
        graph_context_vec = self._retrieve_context(incident_description, search_type="device")
        graph_context_cypher = self.cypher_retriever.retrieve("network attack summary").get("context_text", "")

        combined_context = f"{graph_context_vec}\n\n{graph_context_cypher}"

        template = get_template("incident_summary")
        prompt = template.format(
            incident_context=incident_description,
            graph_context=combined_context,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            classification=classification,
        )

        report = self.llm.generate(prompt)

        return {
            "report": report,
            "date": datetime.now().isoformat(),
            "classification": classification,
        }

    def map_to_mitre(self, behaviors: str = None) -> Dict:
        """
        Map observed behaviors to MITRE ATT&CK framework.

        Args:
            behaviors: Description of observed behaviors (or auto-detect from KG)
        """
        behaviors = behaviors or "All attack types observed in the IoT-23 and CICIoT2023 datasets"

        logger.info("Generating MITRE ATT&CK mapping...")

        graph_context = self._retrieve_context("MITRE ATT&CK techniques IoT attacks", search_type="mitre")
        cypher_context = self.cypher_retriever.retrieve("MITRE ATT&CK mapping").get("context_text", "")

        template = get_template("mitre_mapping")
        prompt = template.format(
            behavior_context=behaviors,
            graph_context=f"{graph_context}\n\n{cypher_context}",
        )

        analysis = self.llm.generate(prompt)

        return {
            "mapping": analysis,
            "behaviors": behaviors,
        }

    def compare_datasets(self) -> Dict:
        """
        Generate a comparative analysis between IoT-23 and CICIoT2023.
        """
        logger.info("Generating dataset comparison...")

        from src.services.graph_embeddings.cypher_queries import compare_datasets
        comparison_data = compare_datasets()

        comparison_context = ""
        if comparison_data:
            comparison_context = "Dataset comparison data:\n"
            for r in comparison_data:
                comparison_context += f"  {r['dataset']:15s} | {r['category']:25s} | {r['count']:,} flows\n"

        graph_context = self._retrieve_context("IoT-23 vs CICIoT2023 comparison", search_type="device")

        template = get_template("dataset_comparison")
        prompt = template.format(
            comparison_context=comparison_context,
            graph_context=graph_context,
        )

        analysis = self.llm.generate(prompt)

        return {
            "analysis": analysis,
            "comparison_data": comparison_data,
        }

    def investigate(self, query: str) -> Dict:
        """
        Free-form threat intelligence investigation.

        Args:
            query: Investigation question or topic

        Returns:
            Dict with investigation results
        """
        logger.info(f"Investigation: {query}")

        # Multi-retrieval for comprehensive context
        multi_result = self.vector_retriever.multi_search(query)
        cypher_result = self.cypher_retriever.retrieve(query)

        combined_context = (
            f"{multi_result.get('context_text', '')}\n\n"
            f"{cypher_result.get('context_text', '')}"
        )

        template = get_template("investigation")
        prompt = template.format(
            query=query,
            graph_context=combined_context,
        )

        analysis = self.llm.generate(prompt)

        return {
            "analysis": analysis,
            "query": query,
            "evidence": {
                "semantic": multi_result.get("results", {}),
                "structured": cypher_result.get("results", []),
            },
        }

    def generate_full_report(self) -> str:
        """
        Generate a comprehensive security assessment report covering
        all aspects of the IoT network.
        """
        logger.info("Generating comprehensive security assessment report...")

        sections = []

        # 1. Executive Summary
        summary = self.investigate("Overall IoT network security threat assessment summary")
        sections.append("# IoT Network Security Assessment Report")
        sections.append(f"\n## Executive Summary\n{summary['analysis'][:1000]}")

        # 2. Attack Landscape
        attacks = self.investigate("What are all the attack types and their frequency?")
        sections.append(f"\n## Attack Landscape\n{attacks['analysis'][:1500]}")

        # 3. MITRE Mapping
        mitre = self.map_to_mitre()
        sections.append(f"\n## MITRE ATT&CK Mapping\n{mitre['mapping'][:1500]}")

        # 4. Dataset Comparison
        comparison = self.compare_datasets()
        sections.append(f"\n## Dataset Comparison\n{comparison['analysis'][:1500]}")

        # 5. Recommendations
        recs = self.investigate("What are the top security recommendations for this IoT network?")
        sections.append(f"\n## Recommendations\n{recs['analysis'][:1000]}")

        full_report = "\n".join(sections)
        logger.info(f"Full report generated: {len(full_report)} characters")

        return full_report


