"""Application-facing operations for local job tracking."""

from __future__ import annotations

from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.storage.local_store import LocalStore
from modules.storage.models import StoredAnalysis, utc_now
from modules.tracker.status import JobStatus


class JobTracker:
    """Create, update, and retrieve local application records."""

    def __init__(self, store: LocalStore | None = None) -> None:
        self.store = store or LocalStore()

    def add_analysis(
        self,
        analysis: JobAnalysisSchema,
        job_title: str = "",
        company: str = "",
        tailor: ResumeTailorOutput | None = None,
        notes: str = "",
        privacy_acknowledged: bool = False,
    ) -> StoredAnalysis:
        """Store a reviewed analysis without raw resume or vacancy text."""
        record = StoredAnalysis(
            job_title=job_title,
            company=company,
            status=JobStatus.GOOD_FIT if analysis.should_apply() else JobStatus.ANALYZED,
            analysis=analysis,
            tailor=tailor,
            notes=notes,
            privacy_acknowledged=privacy_acknowledged,
        )
        return self.store.save(record)

    def change_status(self, record_id: str, status: JobStatus | str) -> StoredAnalysis:
        """Change a record status after validating the target state."""
        record = self.store.get(record_id)
        if record is None:
            raise KeyError(f"Analise nao encontrada: {record_id}")
        record.status = JobStatus(status)
        record.updated_at = utc_now()
        return self.store.save(record)

    def list_analyses(self) -> list[StoredAnalysis]:
        """Return the stored history."""
        return self.store.list_analyses()
