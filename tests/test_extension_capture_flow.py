import pytest
from modules.local_api import (
    ApplicationBatchPayload,
    BrowserCapturePayload,
    CompanionCaptureStore,
    LocalCompanionService,
)
from modules.memory import CareerMemory, MemoryStore
from modules.opportunities import OpportunityStore
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker


def test_previously_applied_jobs_are_imported_to_tracker_and_memory(tmp_path):
    tracker = JobTracker(LocalStore(tmp_path / "history.json"))
    memory = CareerMemory(MemoryStore(tmp_path / "memory.jsonl"))
    service = LocalCompanionService(
        capture_store=CompanionCaptureStore(tmp_path / "captures.jsonl"),
        opportunity_store=OpportunityStore(tmp_path / "opportunities.json"),
        memory=memory,
        tracker=tracker,
        context_path=tmp_path / "context.json",
    )
    payload = ApplicationBatchPayload(
        applications=[
            BrowserCapturePayload(
                page_title="Analista Python Junior",
                job_title="Analista Python Junior",
                company="Example",
                url="https://jobs.example/applied/1",
                description="Vaga Python SQL remota",
            ),
            BrowserCapturePayload(
                page_title="Estágio em Dados",
                job_title="Estágio em Dados",
                company="Data Example",
                url="https://jobs.example/applied/2",
                description="Estágio Python Power BI",
            ),
        ]
    )

    response = service.import_applications(payload)

    assert "2 candidaturas processadas: 2 novas" in response.message
    assert len(tracker.list_analyses()) == 2
    assert len(memory.store.list_memory_items(kind="opportunity")) == 2

    repeated = service.import_applications(payload)

    assert "2 candidaturas processadas: 0 novas e 2 já existentes" in repeated.message
    assert len(tracker.list_analyses()) == 2
    assert len(service.capture_store.list()) == 2
    assert len(memory.store.list_memory_items(kind="opportunity")) == 2


def test_changed_capture_marks_previous_artifacts_stale(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    service = LocalCompanionService(
        capture_store=CompanionCaptureStore(tmp_path / "captures.jsonl"),
        opportunity_store=OpportunityStore(tmp_path / "opportunities.json"),
        memory=CareerMemory(MemoryStore(tmp_path / "memory.jsonl")),
        tracker=JobTracker(LocalStore(tmp_path / "history.json")),
        context_path=tmp_path / "context.json",
    )
    original = BrowserCapturePayload(
        page_title="Analista de Dados",
        job_title="Analista de Dados",
        company="Empresa Exemplo",
        url="https://jobs.example/stale",
        description="Python",
    )

    first = service.capture_job(original)
    changed = service.capture_job(original.model_copy(update={"description": "Python e SQL"}))

    assert first.artifact_status == "current"
    assert changed.capture_id == first.capture_id
    assert changed.artifact_status == "stale"
    assert "recalculados" in changed.stale_reason
