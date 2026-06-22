"""Pure dashboard metrics built from local tracker records."""

from __future__ import annotations

from collections import Counter
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from modules.core.opportunity_identity import source_domain
from modules.storage.models import StoredAnalysis
from modules.tracker.status import JobStatus


class DashboardMetrics(BaseModel):
    """Summary displayed by the initial local dashboard."""

    model_config = ConfigDict(extra="forbid")

    total_analyzed: int = 0
    average_match_score: float = 0
    average_ats_score: float = 0
    average_opportunity_fit: float = 0
    recommended_to_apply: int = 0
    high_risk: int = 0
    latest: list[StoredAnalysis] = Field(default_factory=list)


class FunnelStageMetric(BaseModel):
    """Single application funnel stage."""

    model_config = ConfigDict(extra="forbid")

    status: str
    label: str
    count: int


class FunnelConversionMetric(BaseModel):
    """Conversion rate between two funnel stages."""

    model_config = ConfigDict(extra="forbid")

    from_status: str
    to_status: str
    rate: float


class ApplicationFunnelMetrics(BaseModel):
    """Aggregated application funnel metrics."""

    model_config = ConfigDict(extra="forbid")

    stages: list[FunnelStageMetric] = Field(default_factory=list)
    conversion_rates: list[FunnelConversionMetric] = Field(default_factory=list)


class SourcePerformanceMetric(BaseModel):
    """Aggregated performance for a source/domain."""

    model_config = ConfigDict(extra="forbid")

    name: str
    saved: int = 0
    applied: int = 0
    interviews: int = 0
    average_match: float = 0
    top_requirements: list[str] = Field(default_factory=list)


def calculate_dashboard_metrics(records: list[StoredAnalysis]) -> DashboardMetrics:
    """Calculate stable metrics for an empty or populated history."""
    if not records:
        return DashboardMetrics()

    total = len(records)
    return DashboardMetrics(
        total_analyzed=total,
        average_match_score=round(sum(item.analysis.match_score for item in records) / total, 1),
        average_ats_score=round(sum(item.analysis.ats_score for item in records) / total, 1),
        average_opportunity_fit=round(
            sum(item.analysis.opportunity_fit_score for item in records) / total,
            1,
        ),
        recommended_to_apply=sum(item.analysis.should_apply() for item in records),
        high_risk=sum(item.analysis.risk_score >= 75 for item in records),
        latest=records[:5],
    )


def filter_dashboard_records(
    records: list[StoredAnalysis],
    *,
    recommendation: str = "",
    modality: str = "",
    seniority: str = "",
    risk: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[StoredAnalysis]:
    """Filter saved analyses using the simple dashboard controls."""

    def risk_matches(record: StoredAnalysis) -> bool:
        score = record.analysis.risk_score
        if risk == "low":
            return score < 40
        if risk == "medium":
            return 40 <= score < 75
        if risk == "high":
            return score >= 75
        return True

    return [
        record
        for record in records
        if (not recommendation or record.analysis.recommendation == recommendation)
        and (not modality or record.modality == modality)
        and (not seniority or record.seniority == seniority)
        and risk_matches(record)
        and (date_from is None or record.created_at.date() >= date_from)
        and (date_to is None or record.created_at.date() <= date_to)
    ]


def rank_applied_requirements(
    records: list[StoredAnalysis], *, limit: int = 20
) -> list[tuple[str, int]]:
    """Rank requirements found in jobs marked as applied."""
    return rank_requirements_by_status(records, status=JobStatus.APPLIED, limit=limit)


def rank_requirements_by_status(
    records: list[StoredAnalysis],
    *,
    status: JobStatus | str | None = None,
    limit: int = 20,
) -> list[tuple[str, int]]:
    """Rank requirements by tracker status or all records when status is omitted."""
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}
    for record in records:
        if not _status_matches(record, status):
            continue
        for requirement in record.requirements:
            _add_count(counts, labels, requirement)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [(labels[key], count) for key, count in ranked]


def rank_requirements_by_source(
    records: list[StoredAnalysis],
    *,
    source: str = "",
    limit: int = 20,
) -> list[tuple[str, str, int]]:
    """Rank requirements grouped by source/domain."""
    counts: Counter[tuple[str, str]] = Counter()
    labels: dict[tuple[str, str], tuple[str, str]] = {}
    normalized_source = source.casefold().strip()
    for record in records:
        for record_source in _record_sources(record):
            if normalized_source and normalized_source != record_source.casefold():
                continue
            for requirement in record.requirements:
                cleaned = requirement.strip()
                key = (record_source.casefold(), cleaned.casefold())
                if cleaned and key[1]:
                    labels[key] = (record_source, cleaned)
                    counts[key] += 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [(labels[key][0], labels[key][1], count) for key, count in ranked]


def rank_missing_requirements(
    records: list[StoredAnalysis], *, limit: int = 20
) -> list[tuple[str, int]]:
    """Rank missing requirements and unsupported ATS keywords."""
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}
    for record in records:
        missing = [
            *record.analysis.missing_requirements,
            *record.analysis.missing_keywords,
            *record.analysis.ats_missing_without_evidence,
        ]
        for requirement in dict.fromkeys(missing):
            _add_count(counts, labels, requirement)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [(labels[key], count) for key, count in ranked]


def rank_critical_gaps(records: list[StoredAnalysis], *, limit: int = 20) -> list[tuple[str, int]]:
    """Rank repeated critical gaps from match analyses."""
    counts: Counter[str] = Counter()
    labels: dict[str, str] = {}
    for record in records:
        gaps = record.analysis.critical_gaps or record.analysis.risk_flags
        for gap in dict.fromkeys(gaps):
            _add_count(counts, labels, gap)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [(labels[key], count) for key, count in ranked]


def calculate_application_funnel(records: list[StoredAnalysis]) -> ApplicationFunnelMetrics:
    """Calculate a compact saved -> applied -> response -> interview -> offer funnel."""
    saved = len(records)
    applied = sum(_at_or_after_applied(record.status) for record in records)
    response = sum(
        record.status
        in {
            JobStatus.FOLLOW_UP,
            JobStatus.INTERVIEW,
            JobStatus.TECHNICAL_TEST,
            JobStatus.REJECTED,
            JobStatus.OFFER,
        }
        for record in records
    )
    interviews = sum(
        record.status in {JobStatus.INTERVIEW, JobStatus.TECHNICAL_TEST, JobStatus.OFFER}
        for record in records
    )
    offers = sum(record.status == JobStatus.OFFER for record in records)
    stages = [
        FunnelStageMetric(status="saved", label="Salvas", count=saved),
        FunnelStageMetric(status="applied", label="Aplicadas", count=applied),
        FunnelStageMetric(status="response", label="Com resposta", count=response),
        FunnelStageMetric(status="interview", label="Entrevistas", count=interviews),
        FunnelStageMetric(status="offer", label="Oferta", count=offers),
    ]
    return ApplicationFunnelMetrics(
        stages=stages,
        conversion_rates=[
            FunnelConversionMetric(
                from_status="saved", to_status="applied", rate=_rate(applied, saved)
            ),
            FunnelConversionMetric(
                from_status="applied", to_status="response", rate=_rate(response, applied)
            ),
            FunnelConversionMetric(
                from_status="response", to_status="interview", rate=_rate(interviews, response)
            ),
            FunnelConversionMetric(
                from_status="interview", to_status="offer", rate=_rate(offers, interviews)
            ),
        ],
    )


def calculate_source_metrics(
    records: list[StoredAnalysis], *, limit: int = 20
) -> list[SourcePerformanceMetric]:
    """Compare sources by volume, progress and average match."""
    buckets: dict[str, list[StoredAnalysis]] = {}
    for record in records:
        for source in _record_sources(record):
            buckets.setdefault(source, []).append(record)

    metrics = []
    for name, bucket in buckets.items():
        requirement_counts = _requirements_counter(bucket)
        top_requirements = [
            label
            for label, _ in sorted(
                requirement_counts.items(), key=lambda item: (-item[1], item[0])
            )[:5]
        ]
        metrics.append(
            SourcePerformanceMetric(
                name=name,
                saved=len(bucket),
                applied=sum(_at_or_after_applied(record.status) for record in bucket),
                interviews=sum(
                    record.status
                    in {JobStatus.INTERVIEW, JobStatus.TECHNICAL_TEST, JobStatus.OFFER}
                    for record in bucket
                ),
                average_match=round(
                    sum(record.analysis.match_score for record in bucket) / len(bucket), 1
                ),
                top_requirements=top_requirements,
            )
        )
    return sorted(metrics, key=lambda item: (-item.applied, -item.saved, item.name))[:limit]


def _status_matches(record: StoredAnalysis, status: JobStatus | str | None) -> bool:
    if status is None or status == "":
        return True
    if status == "high_match":
        return record.analysis.match_score >= 70
    return record.status == JobStatus(status)


def _add_count(counts: Counter[str], labels: dict[str, str], value: str) -> None:
    cleaned = value.strip()
    key = cleaned.casefold()
    if cleaned and key:
        if key not in labels or (labels[key].islower() and not cleaned.islower()):
            labels[key] = cleaned
        counts[key] += 1


def _record_sources(record: StoredAnalysis) -> list[str]:
    domains = [source for source in record.source_domains if source]
    if domains:
        return list(dict.fromkeys(domains))
    urls = record.source_urls or ([record.source_url] if record.source_url else [])
    url_domains = [source_domain(url) for url in urls if source_domain(url)]
    if url_domains:
        return list(dict.fromkeys(url_domains))
    return [record.collection_method]


def _at_or_after_applied(status: JobStatus) -> bool:
    return status in {
        JobStatus.APPLIED,
        JobStatus.MESSAGE_SENT,
        JobStatus.FOLLOW_UP,
        JobStatus.INTERVIEW,
        JobStatus.TECHNICAL_TEST,
        JobStatus.REJECTED,
        JobStatus.OFFER,
    }


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 2) if denominator else 0


def _requirements_counter(records: list[StoredAnalysis]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        for requirement in record.requirements:
            cleaned = requirement.strip()
            if cleaned:
                counts[cleaned] += 1
    return counts
