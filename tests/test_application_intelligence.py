from modules.schemas.job_analysis import JobAnalysisSchema
from modules.storage.models import StoredAnalysis
from modules.tracker.dashboard import (
    calculate_application_funnel,
    calculate_source_metrics,
    rank_critical_gaps,
    rank_missing_requirements,
    rank_requirements_by_source,
    rank_requirements_by_status,
)
from modules.tracker.status import JobStatus


def _record(
    title: str,
    status: JobStatus,
    requirements: list[str],
    source_url: str,
    match_score: int,
    missing: list[str] | None = None,
    critical: list[str] | None = None,
) -> StoredAnalysis:
    return StoredAnalysis(
        job_title=title,
        source_url=source_url,
        source_urls=[source_url],
        source_domains=[source_url.split("/")[2]],
        status=status,
        requirements=requirements,
        privacy_acknowledged=True,
        analysis=JobAnalysisSchema(
            match_score=match_score,
            ats_score=70,
            opportunity_fit_score=70,
            risk_score=20,
            recommendation="apply",
            missing_requirements=missing or [],
            critical_gaps=critical or [],
        ),
    )


def test_application_intelligence_ranks_requirements_gaps_funnel_and_sources() -> None:
    records = [
        _record(
            "Backend 1",
            JobStatus.APPLIED,
            ["Python", "Docker"],
            "https://linkedin.com/jobs/1",
            80,
            missing=["Docker"],
            critical=["Cloud"],
        ),
        _record(
            "Backend 2",
            JobStatus.INTERVIEW,
            ["Python", "FastAPI"],
            "https://gupy.io/jobs/2",
            90,
            missing=["Cloud"],
            critical=["Cloud"],
        ),
    ]

    assert rank_requirements_by_status(records, status=JobStatus.APPLIED)[0] == ("Docker", 1)
    assert ("linkedin.com", "Docker", 1) in rank_requirements_by_source(records)
    assert rank_missing_requirements(records)[0] == ("Cloud", 1)
    assert rank_critical_gaps(records)[0] == ("Cloud", 2)

    funnel = calculate_application_funnel(records)
    assert [stage.status for stage in funnel.stages] == [
        "saved",
        "applied",
        "response",
        "interview",
        "offer",
    ]
    assert funnel.stages[1].count == 2

    sources = calculate_source_metrics(records)
    assert {source.name for source in sources} == {"linkedin.com", "gupy.io"}
