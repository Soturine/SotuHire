"""Pure deterministic metrics used before any optional model-based judging."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from statistics import mean
from typing import Any


def safe_rate(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def rate(values: Iterable[bool]) -> float:
    items = list(values)
    return safe_rate(sum(items), len(items))


def schema_validity(values: Iterable[bool]) -> float:
    return rate(values)


def json_parse_success(payloads: Iterable[object]) -> float:
    results: list[bool] = []
    for payload in payloads:
        if isinstance(payload, dict | list):
            results.append(True)
            continue
        try:
            json.loads(str(payload))
        except (TypeError, ValueError, json.JSONDecodeError):
            results.append(False)
        else:
            results.append(True)
    return rate(results)


def required_field_completion(payload: Mapping[str, Any], required_fields: Sequence[str]) -> float:
    return rate(_path_value(payload, path) not in (None, "", [], {}) for path in required_fields)


def type_correctness(checks: Iterable[tuple[object, type | tuple[type, ...]]]) -> float:
    return rate(isinstance(value, expected) for value, expected in checks)


def fallback_rate(values: Iterable[bool]) -> float:
    return rate(values)


def timeout_rate(error_types: Iterable[str]) -> float:
    return rate(value.casefold() == "timeout" for value in error_types)


def provider_error_rate(error_types: Iterable[str]) -> float:
    return rate(bool(value) for value in error_types)


def field_precision(expected: Iterable[object], actual: Iterable[object]) -> float:
    expected_set, actual_set = _normalized_sets(expected, actual)
    return safe_rate(len(expected_set & actual_set), len(actual_set))


def field_recall(expected: Iterable[object], actual: Iterable[object]) -> float:
    expected_set, actual_set = _normalized_sets(expected, actual)
    return safe_rate(len(expected_set & actual_set), len(expected_set))


def field_f1(expected: Iterable[object], actual: Iterable[object]) -> float:
    precision = field_precision(expected, actual)
    recall = field_recall(expected, actual)
    return safe_rate(2 * precision * recall, precision + recall)


def normalized_exact_match(expected: object, actual: object) -> float:
    return float(_normalize(expected) == _normalize(actual))


def date_accuracy(expected: Iterable[object], actual: Iterable[object]) -> float:
    return field_recall(
        (_normalize_date(value) for value in expected), (_normalize_date(value) for value in actual)
    )


def salary_accuracy(
    expected: float | None, actual: float | None, *, tolerance: float = 0.01
) -> float:
    if expected is None or actual is None:
        return float(expected is actual)
    return float(math.isclose(float(expected), float(actual), rel_tol=tolerance, abs_tol=0.01))


def requirement_classification_accuracy(expected: Iterable[str], actual: Iterable[str]) -> float:
    return _paired_accuracy(expected, actual)


def domain_classification_accuracy(expected: Iterable[str], actual: Iterable[str]) -> float:
    return _paired_accuracy(expected, actual)


def evidence_precision(
    claim_evidence: Mapping[str, Iterable[str]], supported_refs: Iterable[str]
) -> float:
    supported = {_normalize(value) for value in supported_refs}
    cited = {
        _normalize(ref) for refs in claim_evidence.values() for ref in refs if str(ref).strip()
    }
    return safe_rate(len(cited & supported), len(cited))


def evidence_recall(
    claim_evidence: Mapping[str, Iterable[str]], required_refs: Iterable[str]
) -> float:
    required = {_normalize(value) for value in required_refs}
    cited = {
        _normalize(ref) for refs in claim_evidence.values() for ref in refs if str(ref).strip()
    }
    return safe_rate(len(cited & required), len(required))


def unsupported_claim_rate(claim_evidence: Mapping[str, Iterable[str]]) -> float:
    return rate(not any(str(ref).strip() for ref in refs) for refs in claim_evidence.values())


def hallucination_rate(claims: Iterable[str], forbidden_claims: Iterable[str]) -> float:
    claim_items = [_normalize(value) for value in claims]
    forbidden = [_normalize(value) for value in forbidden_claims]
    return rate(any(term and term in claim for term in forbidden) for claim in claim_items)


def source_ref_coverage(claim_evidence: Mapping[str, Iterable[str]]) -> float:
    return rate(any(str(ref).strip() for ref in refs) for refs in claim_evidence.values())


def confirmed_evidence_usage_rate(used_refs: Iterable[str], confirmed_refs: Iterable[str]) -> float:
    used = {_normalize(value) for value in used_refs}
    confirmed = {_normalize(value) for value in confirmed_refs}
    return safe_rate(len(used & confirmed), len(used))


def unconfirmed_claim_rate(
    claim_refs: Mapping[str, Iterable[str]], unconfirmed_refs: Iterable[str]
) -> float:
    unconfirmed = {_normalize(value) for value in unconfirmed_refs}
    return rate(any(_normalize(ref) in unconfirmed for ref in refs) for refs in claim_refs.values())


def brier_score(confidences: Sequence[float], labels: Sequence[int | bool]) -> float:
    _same_length(confidences, labels)
    return (
        mean(
            (float(confidence) - int(label)) ** 2
            for confidence, label in zip(confidences, labels, strict=True)
        )
        if confidences
        else 0.0
    )


def confidence_calibration_error(
    confidences: Sequence[float], labels: Sequence[int | bool], *, bins: int = 10
) -> float:
    _same_length(confidences, labels)
    if not confidences:
        return 0.0
    total_error = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        positions = [
            position
            for position, value in enumerate(confidences)
            if low <= value < high or (index == bins - 1 and value == 1)
        ]
        if not positions:
            continue
        confidence = mean(float(confidences[position]) for position in positions)
        accuracy = mean(int(labels[position]) for position in positions)
        total_error += (len(positions) / len(confidences)) * abs(confidence - accuracy)
    return total_error


def overconfidence_rate(
    confidences: Sequence[float], labels: Sequence[int | bool], *, threshold: float = 0.7
) -> float:
    _same_length(confidences, labels)
    return rate(
        confidence >= threshold and not bool(label)
        for confidence, label in zip(confidences, labels, strict=True)
    )


def underconfidence_rate(
    confidences: Sequence[float], labels: Sequence[int | bool], *, threshold: float = 0.5
) -> float:
    _same_length(confidences, labels)
    return rate(
        confidence < threshold and bool(label)
        for confidence, label in zip(confidences, labels, strict=True)
    )


def confidence_by_group(confidences: Sequence[float], groups: Sequence[str]) -> dict[str, float]:
    _same_length(confidences, groups)
    grouped: dict[str, list[float]] = {}
    for confidence, group in zip(confidences, groups, strict=True):
        grouped.setdefault(group, []).append(float(confidence))
    return {key: mean(values) for key, values in sorted(grouped.items())}


confidence_by_domain = confidence_by_group
confidence_by_provider = confidence_by_group


def human_acceptance_rate(decisions: Iterable[str]) -> float:
    items = list(decisions)
    return safe_rate(sum(value == "accepted" for value in items), len(items))


def human_edit_rate(decisions: Iterable[str]) -> float:
    items = list(decisions)
    return safe_rate(sum(value == "edited" for value in items), len(items))


def human_rejection_rate(decisions: Iterable[str]) -> float:
    items = list(decisions)
    return safe_rate(sum(value == "rejected" for value in items), len(items))


def suggestion_usefulness(ratings: Iterable[str]) -> float:
    weights = {"useful": 1.0, "partial": 0.5, "not_useful": 0.0}
    values = [weights[value] for value in ratings if value in weights]
    return mean(values) if values else 0.0


def mean_score(values: Iterable[float]) -> float:
    items = [float(value) for value in values]
    return mean(items) if items else 0.0


actionability_score = mean_score
clarity_score = mean_score
explanation_score = mean_score


def percentile(values: Iterable[float], quantile: float) -> float:
    items = sorted(float(value) for value in values)
    if not items:
        return 0.0
    position = (len(items) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return items[lower]
    return items[lower] + (items[upper] - items[lower]) * (position - lower)


def latency_p50(values: Iterable[float]) -> float:
    return percentile(values, 0.5)


def latency_p95(values: Iterable[float]) -> float:
    return percentile(values, 0.95)


def estimated_cost(costs: Iterable[float | None]) -> float:
    return sum(float(value) for value in costs if value is not None)


def cost_per_accepted_suggestion(cost: float, accepted: int) -> float:
    return safe_rate(cost, accepted)


def quality_per_cost(quality: float, cost: float) -> float:
    return safe_rate(quality, cost)


def quality_per_latency(quality: float, latency_ms: float) -> float:
    return safe_rate(quality, latency_ms)


def dedup_precision(true_merges: int, false_merges: int) -> float:
    return safe_rate(true_merges, true_merges + false_merges)


def dedup_recall(true_merges: int, missed_duplicates: int) -> float:
    return safe_rate(true_merges, true_merges + missed_duplicates)


def false_merge_rate(false_merges: int, total_merges: int) -> float:
    return safe_rate(false_merges, total_merges)


def missed_duplicate_rate(missed_duplicates: int, total_duplicates: int) -> float:
    return safe_rate(missed_duplicates, total_duplicates)


def _normalize(value: object) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).split())


def _normalize_date(value: object) -> str:
    digits = re.sub(r"[^0-9]", "", str(value))
    return digits[:8]


def _normalized_sets(
    expected: Iterable[object], actual: Iterable[object]
) -> tuple[set[str], set[str]]:
    return ({_normalize(value) for value in expected}, {_normalize(value) for value in actual})


def _paired_accuracy(expected: Iterable[str], actual: Iterable[str]) -> float:
    expected_items, actual_items = list(expected), list(actual)
    if len(expected_items) != len(actual_items):
        return 0.0
    return rate(
        _normalize(left) == _normalize(right)
        for left, right in zip(expected_items, actual_items, strict=True)
    )


def _same_length(left: Sequence[object], right: Sequence[object]) -> None:
    if len(left) != len(right):
        raise ValueError("metric inputs must have the same length")


def _path_value(payload: Mapping[str, Any], path: str) -> Any:
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value
