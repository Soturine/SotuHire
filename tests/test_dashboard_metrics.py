from modules.schemas.job_analysis import JobAnalysisSchema, Recommendation
from modules.storage.models import StoredAnalysis
from modules.tracker.dashboard import calculate_dashboard_metrics


def _record(
    match: int, ats: int, fit: int, risk: int, recommendation: Recommendation
) -> StoredAnalysis:
    return StoredAnalysis(
        analysis=JobAnalysisSchema(
            match_score=match,
            ats_score=ats,
            opportunity_fit_score=fit,
            risk_score=risk,
            recommendation=recommendation,
        )
    )


def test_dashboard_accepts_empty_history():
    metrics = calculate_dashboard_metrics([])

    assert metrics.total_analyzed == 0
    assert metrics.average_match_score == 0


def test_dashboard_calculates_expected_metrics():
    metrics = calculate_dashboard_metrics(
        [
            _record(80, 70, 90, 10, "apply"),
            _record(40, 50, 30, 80, "ignore"),
        ]
    )

    assert metrics.total_analyzed == 2
    assert metrics.average_match_score == 60
    assert metrics.average_ats_score == 60
    assert metrics.average_opportunity_fit == 60
    assert metrics.recommended_to_apply == 1
    assert metrics.high_risk == 1
