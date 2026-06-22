import json
import pytest
from unittest.mock import patch, MagicMock
from src.services.evaluation.ablation import run_ablation_condition, AblationCondition


def test_ablation_condition_enum_has_three_values():
    conditions = list(AblationCondition)
    assert len(conditions) == 3
    names = {c.value for c in conditions}
    assert "cypher_only" in names
    assert "vector_only" in names
    assert "combined" in names


def test_run_ablation_condition_returns_result_dict():
    query = {"id": "q001", "query": "What is Mirai?", "retrieval_type": "attack_description"}
    with patch("src.services.evaluation.ablation.CypherRetriever") as MockCypher, \
         patch("src.services.evaluation.ablation.VectorGraphRetriever") as MockVector:
        MockCypher.return_value.retrieve.return_value = {
            "context_text": "Mirai is a botnet", "results": [{"name": "Mirai"}]
        }
        MockVector.return_value.retrieve.return_value = {
            "context_text": "Mirai malware", "results": [{"name": "Mirai botnet"}]
        }
        result = run_ablation_condition(query, AblationCondition.CYPHER_ONLY)

    assert result["query_id"] == "q001"
    assert result["condition"] == "cypher_only"
    assert "context_text" in result
    assert "latency_ms" in result
