"""Application-facing operations for local job tracking."""

from __future__ import annotations

from modules.core.collection_method import CollectionMethod
from modules.core.opportunity_identity import normalize_opportunity_url
from modules.core.text_utils import normalize_text
from modules.memory import CareerMemory, MemoryStore
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.storage.local_store import LocalStore
from modules.storage.models import StoredAnalysis, utc_now
from modules.tracker.status import JobStatus


class JobTracker:
    """Create, update, and retrieve local application records."""

    def __init__(self, store: LocalStore | None = None) -> None:
        self.store = store or LocalStore()
        memory_path = self.store.path.parent / "memory" / "career-memory.jsonl"
        self.memory = CareerMemory(MemoryStore(memory_path))

    def add_analysis(
        self,
        analysis: JobAnalysisSchema,
        job_title: str = "",
        company: str = "",
        modality: str = "",
        seniority: str = "",
        tailor: ResumeTailorOutput | None = None,
        notes: str = "",
        privacy_acknowledged: bool = False,
        source_url: str = "",
        collection_method: CollectionMethod = "manual_url",
        requirements: list[str] | None = None,
    ) -> StoredAnalysis:
        """Store a reviewed analysis without raw resume or vacancy text."""
        existing = self._find_duplicate(job_title, company, source_url)
        if existing is not None:
            previous_status = existing.status
            saved = self.store.save(
                existing.model_copy(
                    update={
                        "job_title": job_title or existing.job_title,
                        "company": company or existing.company,
                        "modality": modality or existing.modality,
                        "seniority": seniority or existing.seniority,
                        "source_url": source_url or existing.source_url,
                        "collection_method": collection_method,
                        "requirements": requirements
                        or list(analysis.missing_keywords)
                        or existing.requirements,
                        "analysis": analysis,
                        "tailor": tailor or existing.tailor,
                        "notes": notes or existing.notes,
                        "privacy_acknowledged": privacy_acknowledged
                        or existing.privacy_acknowledged,
                        "status": (
                            JobStatus.APPLIED
                            if existing.status == JobStatus.APPLIED
                            else (
                                JobStatus.GOOD_FIT
                                if analysis.should_apply()
                                else JobStatus.ANALYZED
                            )
                        ),
                        "updated_at": utc_now(),
                    }
                )
            )
            self.memory.remember_analysis(
                analysis,
                job_title=saved.job_title,
                company=saved.company,
                source_id=saved.id,
            )
            if saved.status != previous_status:
                self.memory.remember_tracker_event(
                    record_id=saved.id,
                    status=saved.status.value,
                    job_title=saved.job_title,
                    company=saved.company,
                )
            return saved
        record = StoredAnalysis(
            job_title=job_title,
            company=company,
            modality=modality,
            seniority=seniority,
            status=JobStatus.GOOD_FIT if analysis.should_apply() else JobStatus.ANALYZED,
            analysis=analysis,
            tailor=tailor,
            notes=notes,
            privacy_acknowledged=privacy_acknowledged,
            source_url=source_url,
            collection_method=collection_method,
            requirements=requirements or list(analysis.missing_keywords),
        )
        saved = self.store.save(record)
        self.memory.remember_analysis(
            analysis,
            job_title=job_title,
            company=company,
            source_id=saved.id,
        )
        self.memory.remember_opportunity(
            title=job_title,
            company=company,
            source_id=saved.id,
            details=notes,
            tags=[modality, seniority, analysis.recommendation],
        )
        self.memory.remember_tracker_event(
            record_id=saved.id,
            status=saved.status.value,
            job_title=job_title,
            company=company,
        )
        return saved

    def change_status(self, record_id: str, status: JobStatus | str) -> StoredAnalysis:
        """Change a record status after validating the target state."""
        record = self.store.get(record_id)
        if record is None:
            raise KeyError(f"Analise nao encontrada: {record_id}")
        record.status = JobStatus(status)
        record.updated_at = utc_now()
        saved = self.store.save(record)
        self.memory.remember_tracker_event(
            record_id=saved.id,
            status=saved.status.value,
            job_title=saved.job_title,
            company=saved.company,
        )
        return saved

    def add_existing_application(
        self,
        *,
        job_title: str,
        company: str = "",
        source_url: str = "",
        notes: str = "",
        collection_method: CollectionMethod = "browser_assisted_capture",
        requirements: list[str] | None = None,
        modality: str = "",
        seniority: str = "",
    ) -> StoredAnalysis:
        """Save a vacancy the user already applied to, including LinkedIn applications."""
        analysis = JobAnalysisSchema(
            match_score=0,
            ats_score=0,
            opportunity_fit_score=0,
            risk_score=0,
            recommendation="save_for_later",
        )
        existing = self._find_duplicate(job_title, company, source_url)
        if existing is not None:
            if existing.status != JobStatus.APPLIED:
                return self.change_status(existing.id, JobStatus.APPLIED)
            return existing
        record = StoredAnalysis(
            job_title=job_title,
            company=company,
            status=JobStatus.APPLIED,
            analysis=analysis,
            notes=notes or f"Candidatura já realizada. Fonte: {source_url}",
            privacy_acknowledged=True,
            source_url=source_url,
            collection_method=collection_method,
            requirements=requirements or [],
            modality=modality,
            seniority=seniority,
        )
        saved = self.store.save(record)
        self.memory.remember_opportunity(
            title=job_title,
            company=company,
            source="existing_application",
            source_id=saved.id,
            details=saved.notes,
            tags=["applied"],
        )
        self.memory.remember_tracker_event(
            record_id=saved.id,
            status=JobStatus.APPLIED.value,
            job_title=job_title,
            company=company,
        )
        return saved

    def list_analyses(self) -> list[StoredAnalysis]:
        """Return the stored history."""
        return self.store.list_analyses()

    def _find_duplicate(
        self,
        job_title: str,
        company: str,
        source_url: str,
    ) -> StoredAnalysis | None:
        normalized_url = normalize_opportunity_url(source_url)
        identity = (normalize_text(job_title), normalize_text(company))
        for record in self.store.list_analyses():
            if normalized_url and normalize_opportunity_url(record.source_url) == normalized_url:
                return record
            if identity != ("", "") and identity == (
                normalize_text(record.job_title),
                normalize_text(record.company),
            ):
                return record
        return None
