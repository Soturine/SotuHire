from __future__ import annotations

from datetime import UTC, datetime, timedelta

from modules.schemas.job_analysis import JobAnalysisSchema
from modules.storage.models import StoredAnalysis
from modules.tracker.career_analytics import build_career_analytics
from modules.tracker.status import JobStatus


def _record(status: JobStatus, *, hours: int, source: str = "example.com") -> StoredAnalysis:
    applied = datetime(2026, 1, 1, tzinfo=UTC)
    history = [{"status": "applied", "at": applied.isoformat()}]
    if status in {JobStatus.INTERVIEW, JobStatus.OFFER}:
        history.append(
            {"status": "interview", "at": (applied + timedelta(hours=hours)).isoformat()}
        )
    if status == JobStatus.OFFER:
        history.append(
            {"status": "offer", "at": (applied + timedelta(hours=hours + 2)).isoformat()}
        )
    return StoredAnalysis(
        job_title="Pessoa desenvolvedora Python",
        status=status,
        source_domains=[source],
        applied_at=applied,
        created_at=applied,
        updated_at=applied + timedelta(hours=hours + 2),
        stage_history=history,
        analysis=JobAnalysisSchema(
            match_score=80,
            ats_score=70,
            opportunity_fit_score=75,
            risk_score=10,
            recommendation="apply",
        ),
    )


def test_analytics_discloses_sample_period_denominators_and_no_causality() -> None:
    report = build_career_analytics(
        [_record(JobStatus.INTERVIEW, hours=24), _record(JobStatus.OFFER, hours=48)]
    )
    assert report.n == 2
    assert report.period_start is not None and report.period_end is not None
    assert report.funnel["applied"] == 2
    assert report.funnel["interview"] == 2
    assert report.funnel["offer"] == 1
    assert next(item for item in report.rates if item.name == "offer_rate").denominator == 2
    assert report.median_time_to_response_hours == 36
    assert report.by_source[0].sample_warning
    assert "causalidade" in report.interpretation
