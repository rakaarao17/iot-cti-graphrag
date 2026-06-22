from src.services.evaluation.classification_metrics import compute_classification_metrics, ClassificationResult
from src.services.evaluation.retrieval_metrics import compute_mrr, compute_hit_at_k


def test_classification_metrics_perfect_predictions():
    y_true = ["Benign", "DDoS", "Benign", "Mirai"]
    y_pred = ["Benign", "DDoS", "Benign", "Mirai"]
    result = compute_classification_metrics(y_true, y_pred)
    assert result.macro_f1 == 1.0
    assert result.per_class["Benign"]["f1"] == 1.0


def test_classification_metrics_all_wrong():
    y_true = ["Benign", "Benign"]
    y_pred = ["DDoS", "Mirai"]
    result = compute_classification_metrics(y_true, y_pred)
    assert result.macro_f1 == 0.0


def test_mrr_first_result_relevant():
    result = compute_mrr(
        ranked_results=["doc1", "doc2", "doc3"],
        relevant_ids={"doc1"},
    )
    assert result == 1.0


def test_mrr_second_result_relevant():
    result = compute_mrr(
        ranked_results=["doc2", "doc1", "doc3"],
        relevant_ids={"doc1"},
    )
    assert abs(result - 0.5) < 1e-6


def test_mrr_no_relevant_result():
    result = compute_mrr(
        ranked_results=["doc2", "doc3"],
        relevant_ids={"doc1"},
    )
    assert result == 0.0


def test_hit_at_k_found():
    assert compute_hit_at_k(["a", "b", "c"], {"b"}, k=3) == 1


def test_hit_at_k_not_found_within_k():
    assert compute_hit_at_k(["a", "b", "c", "d"], {"d"}, k=2) == 0
