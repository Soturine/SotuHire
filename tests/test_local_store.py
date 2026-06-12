import pytest
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.storage.local_store import LocalStore
from modules.storage.models import StoredAnalysis


def _analysis() -> JobAnalysisSchema:
    return JobAnalysisSchema(
        match_score=80,
        ats_score=70,
        opportunity_fit_score=90,
        risk_score=10,
        recommendation="apply",
    )


def test_local_store_saves_and_reads_analysis(tmp_path):
    store = LocalStore(tmp_path / "history.json")
    record = StoredAnalysis(
        job_title="Backend",
        analysis=_analysis(),
        privacy_acknowledged=True,
    )

    store.save(record)

    assert store.get(record.id) == record
    assert store.list_analyses()[0].job_title == "Backend"


def test_local_store_requires_privacy_acknowledgement(tmp_path):
    store = LocalStore(tmp_path / "history.json")

    with pytest.raises(ValueError):
        store.save(StoredAnalysis(analysis=_analysis()))


def test_local_store_accepts_missing_file(tmp_path):
    assert LocalStore(tmp_path / "missing.json").list_analyses() == []
