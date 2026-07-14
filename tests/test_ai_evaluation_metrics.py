import pytest
from modules.ai.evaluation import metrics


def test_precision_recall_f1_and_structural_metrics() -> None:
    assert metrics.field_precision(["Python", "SQL"], ["python", "Docker"]) == 0.5
    assert metrics.field_recall(["Python", "SQL"], ["python", "Docker"]) == 0.5
    assert metrics.field_f1(["Python", "SQL"], ["python", "Docker"]) == 0.5
    assert metrics.schema_validity([True, True, False]) == pytest.approx(2 / 3)
    assert metrics.json_parse_success(['{"ok": true}', "invalid"]) == 0.5
    assert metrics.required_field_completion({"a": {"b": 1}}, ["a.b", "missing"]) == 0.5


def test_evidence_claim_and_calibration_metrics() -> None:
    claims = {"claim-a": ["ref-1"], "claim-b": []}
    assert metrics.evidence_precision(claims, ["ref-1", "ref-2"]) == 1.0
    assert metrics.evidence_recall(claims, ["ref-1", "ref-2"]) == 0.5
    assert metrics.unsupported_claim_rate(claims) == 0.5
    assert metrics.hallucination_rate(["Python", "invented doctorate"], ["doctorate"]) == 0.5
    assert metrics.brier_score([0.8, 0.2], [1, 0]) == pytest.approx(0.04)
    assert metrics.confidence_calibration_error([0.8, 0.2], [1, 0], bins=2) == pytest.approx(0.2)
    assert metrics.overconfidence_rate([0.9, 0.8], [0, 1]) == 0.5
    assert metrics.underconfidence_rate([0.2, 0.8], [1, 1]) == 0.5


def test_utility_operations_and_dedupe_metrics() -> None:
    assert metrics.human_acceptance_rate(["accepted", "rejected"]) == 0.5
    assert metrics.human_edit_rate(["edited", "accepted"]) == 0.5
    assert metrics.human_rejection_rate(["rejected", "ignored"]) == 0.5
    assert metrics.suggestion_usefulness(["useful", "partial", "not_useful"]) == 0.5
    assert metrics.latency_p50([10, 20, 30]) == 20
    assert metrics.latency_p95([10, 20, 30]) == 29
    assert metrics.estimated_cost([0.1, None, 0.2]) == pytest.approx(0.3)
    assert metrics.dedup_precision(8, 2) == 0.8
    assert metrics.dedup_recall(8, 2) == 0.8
    assert metrics.false_merge_rate(2, 10) == 0.2
    assert metrics.missed_duplicate_rate(2, 10) == 0.2
