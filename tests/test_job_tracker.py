import pytest
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.storage.database import connect_database
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
    assert record.job_snapshot_id
    assert record.match_analysis_snapshot_id
    assert [item["status"] for item in updated.stage_history] == ["good_fit", "interview"]
    with connect_database(tmp_path / "sotuhire.db") as connection:
        application = connection.execute(
            "SELECT job_snapshot_id, match_analysis_snapshot_id, status FROM applications"
        ).fetchone()
        assert tuple(application) == (
            record.job_snapshot_id,
            record.match_analysis_snapshot_id,
            "interview",
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM application_events WHERE application_id = ?", (record.id,)
            ).fetchone()[0]
            == 2
        )


def test_tracker_links_exact_resume_job_and_tailor_snapshots(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    record = tracker.add_analysis(
        _analysis(),
        job_title="Backend",
        company="Acme",
        source_url="https://example.com/jobs/1",
        job_text="Texto original da vaga",
        resume_text="Currículo realmente usado",
        privacy_acknowledged=True,
    )

    assert record.resume_snapshot_id
    with connect_database(tmp_path / "sotuhire.db") as connection:
        job = connection.execute(
            "SELECT raw_text FROM job_snapshots WHERE snapshot_id = ?",
            (record.job_snapshot_id,),
        ).fetchone()
        resume = connection.execute(
            "SELECT content FROM resume_snapshots WHERE snapshot_id = ?",
            (record.resume_snapshot_id,),
        ).fetchone()
        assert job[0] == "Texto original da vaga"
        assert resume[0] == "Currículo realmente usado"


def test_tracker_rejects_unknown_status(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    record = tracker.add_analysis(_analysis(), privacy_acknowledged=True)

    with pytest.raises(ValueError):
        tracker.change_status(record.id, "unknown")


def test_tracker_records_existing_linkedin_application_in_memory(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))

    record = tracker.add_existing_application(
        job_title="Backend",
        company="Acme",
        source_url="https://www.linkedin.com/jobs/view/123",
    )

    assert record.status == JobStatus.APPLIED
    assert any(item.kind == "opportunity" for item in tracker.memory.store.list_memory_items())
    assert any(
        item.kind == "tracker_event" and "applied" in item.tags
        for item in tracker.memory.store.list_memory_items()
    )
