from modules.schemas.job_analysis import JobAnalysisSchema, Recommendation
from modules.storage.local_store import LocalStore
from modules.storage.models import StoredAnalysis
from modules.tracker.dashboard import calculate_dashboard_metrics, filter_dashboard_records
from modules.tracker.job_tracker import JobTracker


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


def test_dashboard_filters_recommendation_modality_seniority_and_risk():
    recommended = _record(80, 70, 90, 10, "apply").model_copy(
        update={"modality": "remote", "seniority": "junior"}
    )
    ignored = _record(40, 50, 30, 80, "ignore").model_copy(
        update={"modality": "onsite", "seniority": "senior"}
    )

    filtered = filter_dashboard_records(
        [recommended, ignored],
        recommendation="apply",
        modality="remote",
        seniority="junior",
        risk="low",
    )

    assert filtered == [recommended]


def test_saved_analysis_appears_in_history_and_changes_dashboard(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    before = calculate_dashboard_metrics(tracker.list_analyses())

    tracker.add_analysis(
        _record(85, 80, 75, 20, "apply").analysis,
        job_title="Frontend Júnior",
        modality="remote",
        seniority="junior",
        privacy_acknowledged=True,
    )
    after = calculate_dashboard_metrics(tracker.list_analyses())

    assert before.total_analyzed == 0
    assert after.total_analyzed == 1
    assert after.latest[0].job_title == "Frontend Júnior"
