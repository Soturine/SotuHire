import pytest
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker
from modules.tracker.status import JobStatus


def _analysis() -> JobAnalysisSchema:
    return JobAnalysisSchema(
        match_score=85,
        ats_score=80,
        opportunity_fit_score=90,
        risk_score=5,
        recommendation="apply",
    )


def test_tracker_adds_analysis_and_changes_status(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    record = tracker.add_analysis(
        _analysis(),
        job_title="Backend",
        company="Acme",
        privacy_acknowledged=True,
    )

    updated = tracker.change_status(record.id, JobStatus.INTERVIEW)

    assert record.status == JobStatus.GOOD_FIT
    assert updated.status == JobStatus.INTERVIEW
    assert tracker.list_analyses()[0].company == "Acme"


def test_tracker_rejects_unknown_status(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    record = tracker.add_analysis(_analysis(), privacy_acknowledged=True)

    with pytest.raises(ValueError):
        tracker.change_status(record.id, "unknown")
