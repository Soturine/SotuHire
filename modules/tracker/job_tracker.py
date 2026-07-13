"""Application-facing operations for local job tracking."""

from __future__ import annotations

from typing import Any

from modules.core.collection_method import CollectionMethod
from modules.core.opportunity_identity import same_opportunity, source_domain
from modules.memory import CareerMemory, MemoryStore
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.storage.applications import ApplicationRecord, ApplicationRepository
from modules.storage.local_store import LocalStore
from modules.storage.models import StoredAnalysis, utc_now
from modules.storage.snapshots import AnalysisSnapshot, JobSnapshot, ResumeSnapshot, SnapshotStore
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
        job_text: str = "",
        resume_text: str = "",
        profile_id: str = "default",
        resume_variant_id: str = "master",
        source_capture_id: str = "",
        trace: dict[str, Any] | None = None,
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
                        "source_urls": _merge_sources(
                            existing.source_urls or [existing.source_url], source_url
                        ),
                        "source_domains": _merge_domains(
                            existing.source_domains, existing.source_url, source_url
                        ),
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
                        "source_capture_id": source_capture_id or existing.source_capture_id,
                    }
                )
            )
            saved = self._persist_reliable_state(
                saved,
                job_text=job_text,
                resume_text=resume_text,
                profile_id=profile_id,
                resume_variant_id=resume_variant_id,
                trace=trace,
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
            source_urls=_merge_sources([], source_url),
            source_domains=_merge_domains([], source_url),
            collection_method=collection_method,
            requirements=requirements or list(analysis.missing_keywords),
            source_capture_id=source_capture_id,
        )
        saved = self.store.save(record)
        saved = self._persist_reliable_state(
            saved,
            job_text=job_text,
            resume_text=resume_text,
            profile_id=profile_id,
            resume_variant_id=resume_variant_id,
            trace=trace,
        )
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
        record.stage_history = [
            *record.stage_history,
            {"status": record.status.value, "at": record.updated_at.isoformat()},
        ]
        saved = self.store.save(record)
        self._persist_application(saved)
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
        source_capture_id: str = "",
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
            status_changed = existing.status != JobStatus.APPLIED
            applied_at = existing.applied_at or utc_now()
            saved = self.store.save(
                existing.model_copy(
                    update={
                        "status": JobStatus.APPLIED,
                        "source_url": existing.source_url or source_url,
                        "source_urls": _merge_sources(
                            existing.source_urls or [existing.source_url], source_url
                        ),
                        "source_domains": _merge_domains(
                            existing.source_domains, existing.source_url, source_url
                        ),
                        "requirements": _merge_unique(existing.requirements, requirements or []),
                        "modality": existing.modality or modality,
                        "seniority": existing.seniority or seniority,
                        "updated_at": utc_now(),
                        "applied_at": applied_at,
                        "source_capture_id": source_capture_id or existing.source_capture_id,
                        "stage_history": [
                            *existing.stage_history,
                            {"status": JobStatus.APPLIED.value, "at": applied_at.isoformat()},
                        ],
                    }
                )
            )
            saved = self._persist_reliable_state(saved)
            if status_changed:
                self.memory.remember_tracker_event(
                    record_id=saved.id,
                    status=saved.status.value,
                    job_title=saved.job_title,
                    company=saved.company,
                )
            return saved
        applied_at = utc_now()
        record = StoredAnalysis(
            job_title=job_title,
            company=company,
            status=JobStatus.APPLIED,
            analysis=analysis,
            notes=notes or f"Candidatura já realizada. Fonte: {source_url}",
            privacy_acknowledged=True,
            source_url=source_url,
            source_urls=_merge_sources([], source_url),
            source_domains=_merge_domains([], source_url),
            collection_method=collection_method,
            requirements=requirements or [],
            modality=modality,
            seniority=seniority,
            source_capture_id=source_capture_id,
            applied_at=applied_at,
            stage_history=[{"status": JobStatus.APPLIED.value, "at": applied_at.isoformat()}],
        )
        saved = self.store.save(record)
        saved = self._persist_reliable_state(saved)
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

    def _persist_reliable_state(
        self,
        record: StoredAnalysis,
        *,
        job_text: str = "",
        resume_text: str = "",
        profile_id: str = "default",
        resume_variant_id: str = "master",
        trace: dict[str, Any] | None = None,
    ) -> StoredAnalysis:
        """Link the mutable tracker card to immutable evidence snapshots."""
        database = self.store.path.parent / "sotuhire.db"
        snapshots = SnapshotStore(database)
        job_snapshot = snapshots.create_job(
            JobSnapshot(
                opportunity_id=record.id,
                title=record.job_title,
                organization=record.company,
                location=record.modality,
                description=job_text or record.notes,
                source_url=record.source_url,
                source_refs=record.source_urls,
                source_kind=record.collection_method,
                raw_text=job_text,
                structured_data={
                    "requirements": record.requirements,
                    "seniority": record.seniority,
                    "modality": record.modality,
                },
            )
        )
        resume_snapshot = None
        if resume_text.strip():
            resume_snapshot = snapshots.create_resume(
                ResumeSnapshot(
                    profile_id=profile_id,
                    resume_variant_id=resume_variant_id,
                    title="Currículo usado na análise",
                    content=resume_text,
                )
            )
        metadata = trace or {}
        analysis_snapshot = snapshots.create_analysis(
            AnalysisSnapshot(
                analysis_type="match",
                job_snapshot_id=job_snapshot.snapshot_id,
                resume_snapshot_id=resume_snapshot.snapshot_id if resume_snapshot else "",
                provider_requested=str(metadata.get("provider_requested", "local")),
                provider_used=str(metadata.get("provider_used", "local")),
                model_requested=str(metadata.get("model_requested", "local")),
                model_used=str(metadata.get("model_used", "local")),
                prompt_id=str(metadata.get("prompt_id", "match_analysis_evidence_based_v1")),
                prompt_version=str(metadata.get("prompt_version", "1.0.0")),
                fallback_used=bool(metadata.get("fallback_used", False)),
                result=record.analysis.model_dump(mode="json"),
                evidence_used=list(record.analysis.evidence_used),
                source_refs=record.source_urls,
            )
        )
        ats_snapshot = snapshots.create_analysis(
            AnalysisSnapshot(
                analysis_type="ats",
                job_snapshot_id=job_snapshot.snapshot_id,
                resume_snapshot_id=resume_snapshot.snapshot_id if resume_snapshot else "",
                provider_requested=str(metadata.get("provider_requested", "local")),
                provider_used=str(metadata.get("provider_used", "local")),
                model_requested=str(metadata.get("model_requested", "local")),
                model_used=str(metadata.get("model_used", "local")),
                prompt_id="ats_analysis_v1",
                prompt_version=str(metadata.get("prompt_version", "1.0.0")),
                fallback_used=bool(metadata.get("fallback_used", False)),
                result={
                    "ats_score": record.analysis.ats_score,
                    "present": record.analysis.ats_present_keywords,
                    "missing_without_evidence": record.analysis.ats_missing_without_evidence,
                },
                evidence_used=list(record.analysis.evidence_used),
                source_refs=record.source_urls,
            )
        )
        tailored_snapshot_id = record.tailored_resume_snapshot_id
        if record.tailor is not None:
            tailored = snapshots.create_resume(
                ResumeSnapshot(
                    profile_id=profile_id,
                    resume_variant_id=f"tailored-{record.id}",
                    title=f"Currículo ajustado para {record.job_title or 'oportunidade'}",
                    content=record.tailor.model_dump_json(indent=2),
                    structured_sections=record.tailor.model_dump(mode="json"),
                )
            )
            tailored_snapshot_id = tailored.snapshot_id
        stage_history = record.stage_history or [
            {"status": record.status.value, "at": record.created_at.isoformat()}
        ]
        linked = record.model_copy(
            update={
                "job_snapshot_id": job_snapshot.snapshot_id,
                "resume_snapshot_id": (
                    resume_snapshot.snapshot_id if resume_snapshot else record.resume_snapshot_id
                ),
                "tailored_resume_snapshot_id": tailored_snapshot_id,
                "match_analysis_snapshot_id": analysis_snapshot.snapshot_id,
                "ats_analysis_snapshot_id": ats_snapshot.snapshot_id,
                "stage_history": stage_history,
            }
        )
        saved = self.store.save(linked)
        self._persist_application(saved)
        return saved

    def _persist_application(self, record: StoredAnalysis) -> None:
        database = self.store.path.parent / "sotuhire.db"
        ApplicationRepository(database).save(
            ApplicationRecord(
                id=record.id,
                job_snapshot_id=record.job_snapshot_id,
                resume_snapshot_id=record.resume_snapshot_id,
                tailored_resume_snapshot_id=record.tailored_resume_snapshot_id,
                match_analysis_snapshot_id=record.match_analysis_snapshot_id,
                ats_analysis_snapshot_id=record.ats_analysis_snapshot_id,
                source_capture_id=record.source_capture_id,
                job_title=record.job_title,
                organization=record.company,
                source_url=record.source_url,
                status=record.status.value,
                applied_at=record.applied_at,
                stage_history=record.stage_history,
                contact_history=record.contact_history,
                interview_notes=record.interview_notes,
                follow_up_at=record.follow_up_at,
                outcome=record.outcome,
                outcome_reason=record.outcome_reason,
                payload=record.model_dump(mode="json"),
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
        )

    def _find_duplicate(
        self,
        job_title: str,
        company: str,
        source_url: str,
    ) -> StoredAnalysis | None:
        for record in self.store.list_analyses():
            record_urls = record.source_urls or ([record.source_url] if record.source_url else [])
            if same_opportunity(
                left_title=record.job_title,
                left_company=record.company,
                left_urls=record_urls,
                right_title=job_title,
                right_company=company,
                right_url=source_url,
            ):
                return record
        return None


def _merge_unique(current: list[str], incoming: list[str]) -> list[str]:
    return list(
        dict.fromkeys([*(item for item in current if item), *(item for item in incoming if item)])
    )


def _merge_sources(current: list[str], source_url: str) -> list[str]:
    return _merge_unique(current, [source_url])


def _merge_domains(current: list[str], *source_urls: str) -> list[str]:
    return _merge_unique(current, [source_domain(url) for url in source_urls])
