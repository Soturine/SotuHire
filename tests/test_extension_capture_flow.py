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

    assert "2 candidaturas" in response.message
    assert len(tracker.list_analyses()) == 2
    assert len(memory.store.list_memory_items(kind="opportunity")) == 2
