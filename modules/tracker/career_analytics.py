"""Explainable descriptive career analytics with sample and period disclosure."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from modules.core.text_utils import normalize_text
from modules.matching import policy_for_domain
from modules.storage.models import StoredAnalysis


class AnalyticsRate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    numerator: int
    denominator: int
    rate: float


class AnalyticsSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment: str
    n: int
    applied: int
    interviews: int
    offers: int
    response_rate: float
    interview_rate: float
    offer_rate: float
    average_match: float | None = None
    sample_warning: str = ""


class CareerAnalyticsReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    n: int
    period_start: datetime | None = None
    period_end: datetime | None = None
    funnel: dict[str, int] = Field(default_factory=dict)
    rates: list[AnalyticsRate] = Field(default_factory=list)
    median_time_to_response_hours: float | None = None
    by_source: list[AnalyticsSegment] = Field(default_factory=list)
    by_resume_variant: list[AnalyticsSegment] = Field(default_factory=list)
    by_domain: list[AnalyticsSegment] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    interpretation: str = (
        "Métricas descritivas; não demonstram causalidade nem garantem resultado futuro."
    )


def build_career_analytics(records: list[StoredAnalysis]) -> CareerAnalyticsReport:
    """Aggregate only observed tracker facts and disclose small samples."""
    ordered = sorted(records, key=lambda item: item.created_at)
    applied = [item for item in ordered if _reached(item, "applied")]
    responses = [item for item in applied if _responded(item)]
    interviews = [item for item in applied if _reached(item, "interview")]
    offers = [item for item in applied if _reached(item, "offer")]
    rejected = [item for item in applied if _reached(item, "rejected")]
    durations = [duration for item in responses if (duration := _response_hours(item)) is not None]
    warnings = []
    if len(ordered) < 5:
        warnings.append("Amostra pequena (n<5); não generalize as taxas.")
    if not applied:
        warnings.append("Sem candidaturas aplicadas no período; taxas usam denominador zero.")
    return CareerAnalyticsReport(
        n=len(ordered),
        period_start=ordered[0].created_at if ordered else None,
        period_end=max((item.updated_at for item in ordered), default=None),
        funnel={
            "saved": len(ordered),
            "applied": len(applied),
            "response": len(responses),
            "interview": len(interviews),
            "offer": len(offers),
            "rejected": len(rejected),
        },
        rates=[
            _rate("response_rate", len(responses), len(applied)),
            _rate("interview_rate", len(interviews), len(applied)),
            _rate("offer_rate", len(offers), len(applied)),
        ],
        median_time_to_response_hours=_median(durations),
        by_source=_segments(ordered, _source),
        by_resume_variant=_segments(ordered, _resume_variant),
        by_domain=_segments(ordered, _domain),
        warnings=warnings,
    )


def _segments(records: list[StoredAnalysis], key_fn) -> list[AnalyticsSegment]:  # noqa: ANN001
    grouped: dict[str, list[StoredAnalysis]] = defaultdict(list)
    for record in records:
        grouped[key_fn(record)].append(record)
    result = []
    for name, selected in grouped.items():
        applied = [item for item in selected if _reached(item, "applied")]
        responses = sum(_responded(item) for item in applied)
        interviews = sum(_reached(item, "interview") for item in applied)
        offers = sum(_reached(item, "offer") for item in applied)
        scores = [item.analysis.match_score for item in selected]
        result.append(
            AnalyticsSegment(
                segment=name,
                n=len(selected),
                applied=len(applied),
                interviews=interviews,
                offers=offers,
                response_rate=_ratio(responses, len(applied)),
                interview_rate=_ratio(interviews, len(applied)),
                offer_rate=_ratio(offers, len(applied)),
                average_match=round(sum(scores) / len(scores), 1) if scores else None,
                sample_warning="Amostra pequena (n<5)." if len(selected) < 5 else "",
            )
        )
    return sorted(result, key=lambda item: (-item.n, item.segment))


def _events(record: StoredAnalysis) -> list[tuple[str, datetime]]:
    result: list[tuple[str, datetime]] = []
    for event in record.stage_history:
        try:
            result.append((str(event.get("status", "")), datetime.fromisoformat(str(event["at"]))))
        except (KeyError, TypeError, ValueError):
            continue
    return result


def _reached(record: StoredAnalysis, status: str) -> bool:
    terminal_implies: dict[str, set[str]] = {
        "applied": {
            "applied",
            "message_sent",
            "follow_up",
            "interview",
            "technical_test",
            "offer",
            "rejected",
        },
        "interview": {"interview", "technical_test", "offer"},
        "offer": {"offer"},
        "rejected": {"rejected"},
    }
    statuses = {record.status.value, *(name for name, _ in _events(record))}
    return bool(statuses & terminal_implies.get(status, {status}))


def _responded(record: StoredAnalysis) -> bool:
    return (
        bool(record.contact_history)
        or _reached(record, "interview")
        or record.status.value
        in {
            "message_sent",
            "follow_up",
        }
    )


def _response_hours(record: StoredAnalysis) -> float | None:
    applied_at = record.applied_at
    if applied_at is None:
        applied_at = next((at for status, at in _events(record) if status == "applied"), None)
    response_at = next(
        (
            at
            for status, at in _events(record)
            if status in {"message_sent", "follow_up", "interview", "technical_test", "offer"}
        ),
        None,
    )
    if applied_at is None or response_at is None or response_at < applied_at:
        return None
    return round((response_at - applied_at).total_seconds() / 3600, 2)


def _source(record: StoredAnalysis) -> str:
    if record.source_domains:
        return record.source_domains[0]
    return (urlparse(record.source_url).hostname or "manual").casefold()


def _resume_variant(record: StoredAnalysis) -> str:
    return record.tailored_resume_snapshot_id or record.resume_snapshot_id or "not_recorded"


def _domain(record: StoredAnalysis) -> str:
    text = normalize_text(" ".join([record.job_title, *record.requirements]))
    rules = (
        ("healthcare", ("saude", "enferm", "hospital", "medic", "psicolog")),
        ("education", ("educacao", "professor", "pedagog", "ensino")),
        ("law", ("direito", "jurid", "advog", "oab")),
        ("engineering", ("engenharia", "engenheiro", "crea")),
        ("finance", ("finance", "contab", "fiscal", "banco")),
        ("design", ("design", "arquitet", "ux", "portfolio")),
        ("research", ("pesquisa", "cient", "laboratorio")),
        ("technology", ("software", "python", "dados", "developer", "desenvolv")),
        ("tourism_services", ("turismo", "hotel", "atendimento", "servicos")),
        ("public_exams", ("concurso", "edital", "prova publica")),
    )
    selected = next(
        (domain for domain, markers in rules if any(marker in text for marker in markers)),
        "administration",
    )
    return policy_for_domain(selected).domain


def _rate(name: str, numerator: int, denominator: int) -> AnalyticsRate:
    return AnalyticsRate(
        name=name,
        numerator=numerator,
        denominator=denominator,
        rate=_ratio(numerator, denominator),
    )


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return round((ordered[middle - 1] + ordered[middle]) / 2, 2)


__all__ = ["AnalyticsRate", "AnalyticsSegment", "CareerAnalyticsReport", "build_career_analytics"]
