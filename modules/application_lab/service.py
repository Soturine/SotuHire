"""Application Lab orchestration over existing context, snapshot and tracker engines."""

from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from modules.application_lab.analysis_pipeline import (
    build_local_analysis_products,
    match_result_to_job_analysis,
)
from modules.application_lab.export import resume_plain_text
from modules.application_lab.models import (
    ActionPlanItem,
    ApplicationActionPlan,
    ApplicationAnalysisBundle,
    ApplicationKit,
    ApplicationKitItem,
    ApplicationLabSession,
    ApplicationLabStatus,
    ApplicationReadinessReport,
    ApplicationSuggestion,
    KitItemStatus,
    MasterResume,
    ResumeVariant,
    ResumeVariantChange,
    SuggestionStatus,
    utc_now,
)
from modules.application_lab.repository import ApplicationLabRepository
from modules.context import CareerContextEngine, CareerContextPurpose
from modules.core.dependency_graph import fingerprint_dependencies
from modules.evidence import EvidenceReviewStatus
from modules.professional_assets import (
    AssetStatus,
    AssetType,
    ProfessionalAsset,
    ProfessionalAssetRepository,
)
from modules.storage.applications import ApplicationRecord, ApplicationRepository
from modules.storage.local_store import LocalStore
from modules.storage.models import StoredAnalysis
from modules.storage.snapshots import AnalysisSnapshot, JobSnapshot, ResumeSnapshot, SnapshotStore
from modules.tracker.job_tracker import JobTracker
from modules.tracker.status import JobStatus

ReviewAction = Literal["accepted", "edited", "rejected", "pending"]


class ApplicationLabService:
    """Coordinate a resumable, human-approved application workflow."""

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        repository: ApplicationLabRepository | None = None,
        context_engine: CareerContextEngine | None = None,
        tracker: JobTracker | None = None,
    ) -> None:
        self.repository = repository or ApplicationLabRepository(database_path)
        self.database_path = self.repository.database_path
        self.snapshots = SnapshotStore(self.database_path)
        self.context_engine = context_engine or CareerContextEngine()
        self.tracker = tracker or JobTracker(
            LocalStore(self.database_path.parent / "sotuhire-history.json")
        )
        self.applications = ApplicationRepository(self.database_path)

    def create_session(self, session: ApplicationLabSession) -> ApplicationLabSession:
        """Create a draft session after validating any supplied relational links."""
        if session.master_resume_id:
            self._master(session.master_resume_id)
        if session.job_snapshot_id:
            self._job(session.job_snapshot_id)
        ready = bool(session.master_resume_id and session.job_snapshot_id)
        prepared = session.model_copy(
            update={
                "status": ApplicationLabStatus.READY if ready else ApplicationLabStatus.DRAFT,
                "current_step": max(session.current_step, 5 if ready else 1),
                "updated_at": utc_now(),
            }
        )
        return self.repository.save_session(prepared)

    def update_session(self, session_id: str, changes: dict[str, Any]) -> ApplicationLabSession:
        """Update inputs and invalidate only their dependent workflow steps."""
        current = self._session(session_id)
        allowed = {
            "profile_id",
            "master_resume_id",
            "job_id",
            "job_snapshot_id",
            "current_step",
            "selected_context_refs",
            "status",
        }
        update = {
            key: value for key, value in changes.items() if key in allowed and value is not None
        }
        if "master_resume_id" in update and update["master_resume_id"]:
            self._master(str(update["master_resume_id"]))
        if "job_snapshot_id" in update and update["job_snapshot_id"]:
            self._job(str(update["job_snapshot_id"]))

        inputs_changed = any(
            key in update and update[key] != getattr(current, key)
            for key in ("master_resume_id", "job_snapshot_id", "selected_context_refs")
        )
        if inputs_changed:
            self.repository.mark_analysis_bundle_stale(
                current.analysis_bundle_id,
                "master_resume_job_or_evidence_scope_changed",
            )
            ProfessionalAssetRepository(self.database_path).mark_session_stale(
                session_id,
                "master_resume_job_or_evidence_scope_changed",
            )
            update.update(
                {
                    "readiness_report_id": "",
                    "analysis_bundle_id": "",
                    "dependency_hash": "",
                    "evidence_scope": {},
                    "resume_variant_id": "",
                    "application_kit_id": "",
                    "action_plan_id": "",
                    "tracker_application_id": "",
                    "analysis_run_ids": [],
                    "invalidated_steps": list(range(5, 11)),
                    "status": ApplicationLabStatus.READY,
                }
            )
        update["updated_at"] = utc_now()
        return self.repository.save_session(current.model_copy(update=update))

    def cancel_session(self, session_id: str) -> ApplicationLabSession:
        current = self._session(session_id)
        return self.repository.save_session(
            current.model_copy(
                update={
                    "status": ApplicationLabStatus.CANCELLED,
                    "updated_at": utc_now(),
                }
            )
        )

    def analyze(
        self, session_id: str
    ) -> tuple[ApplicationReadinessReport, list[ApplicationSuggestion], AnalysisSnapshot]:
        """Run Match, ATS, readiness and Tailor directly with independent snapshots."""
        session = self._session(session_id)
        if session.status is ApplicationLabStatus.CANCELLED:
            raise ValueError("Sessão cancelada; reative-a antes de analisar.")
        master = self._master(session.master_resume_id)
        job = self._job(session.job_snapshot_id)
        self.repository.save_session(
            session.model_copy(
                update={"status": ApplicationLabStatus.ANALYZING, "updated_at": utc_now()}
            )
        )
        try:
            context = self.context_engine.build(
                CareerContextPurpose.MATCH,
                query=f"{job.title} {job.description}",
                include_memory=False,
                include_tracker=False,
                include_sources=False,
                include_extension=False,
                include_github=False,
                max_evidence=20,
                selected_evidence_ids=[] if session.selected_context_refs else None,
                selected_source_refs=session.selected_context_refs,
            )
            products = build_local_analysis_products(session, master, job, context)
            scope = products.scope
            selected_evidence = products.selected_evidence
            scoped_master = products.scoped_master
            match_result = products.match_result
            ats_result = products.ats_result
            base_report = products.readiness_report
            tailor_result = products.tailor_result
            dependency = products.dependency
            evidence_scope = scope.model_dump(mode="json")
            resume_snapshot = self._resume_snapshot(
                scoped_master,
                dependency_hash=dependency.digest,
                evidence_scope=evidence_scope,
            )
            source_refs = list(
                dict.fromkeys(
                    [
                        *[item.source_ref for item in selected_evidence if item.source_ref],
                        *job.source_refs,
                    ]
                )
            )
            evidence_used: list[str | dict[str, Any]] = [
                item.source_ref or item.evidence_id for item in selected_evidence
            ]
            match_snapshot = self.snapshots.create_analysis(
                AnalysisSnapshot(
                    analysis_type="application_match",
                    job_snapshot_id=job.snapshot_id,
                    resume_snapshot_id=resume_snapshot.snapshot_id,
                    prompt_id="match_engine_v2_local",
                    prompt_version="2.0.0",
                    result=match_result.model_dump(mode="json"),
                    evidence_used=evidence_used,
                    source_refs=source_refs,
                    dependency_hash=dependency.digest,
                    dependency_inputs=dependency.inputs,
                )
            )
            ats_snapshot = self.snapshots.create_analysis(
                AnalysisSnapshot(
                    analysis_type="application_ats",
                    job_snapshot_id=job.snapshot_id,
                    resume_snapshot_id=resume_snapshot.snapshot_id,
                    prompt_id="ats_rules_local_v1",
                    prompt_version="1.0.0",
                    result=ats_result.model_dump(mode="json"),
                    evidence_used=evidence_used,
                    source_refs=source_refs,
                    dependency_hash=dependency.digest,
                    dependency_inputs=dependency.inputs,
                )
            )
            tailor_snapshot = self.snapshots.create_analysis(
                AnalysisSnapshot(
                    analysis_type="application_tailor",
                    job_snapshot_id=job.snapshot_id,
                    resume_snapshot_id=resume_snapshot.snapshot_id,
                    prompt_id="safe_tailor_rules_local_v1",
                    prompt_version="1.0.0",
                    result=tailor_result.model_dump(mode="json"),
                    evidence_used=evidence_used,
                    source_refs=source_refs,
                    dependency_hash=dependency.digest,
                    dependency_inputs=dependency.inputs,
                )
            )
            bundle_id = uuid4().hex
            readiness_snapshot_id = uuid4().hex
            report = base_report.model_copy(
                update={
                    "dependency_hash": dependency.digest,
                    "provider_metadata": {
                        **base_report.provider_metadata,
                        "analysis_bundle_id": bundle_id,
                        "match_snapshot_id": match_snapshot.snapshot_id,
                        "ats_snapshot_id": ats_snapshot.snapshot_id,
                        "readiness_snapshot_id": readiness_snapshot_id,
                        "tailor_snapshot_id": tailor_snapshot.snapshot_id,
                        "context_evidence_count": len(context.evidence),
                        "selected_evidence_count": len(selected_evidence),
                        "context_warnings": context.warnings,
                    },
                }
            )
            readiness_snapshot = self.snapshots.create_analysis(
                AnalysisSnapshot(
                    snapshot_id=readiness_snapshot_id,
                    analysis_type="application_readiness",
                    job_snapshot_id=job.snapshot_id,
                    resume_snapshot_id=resume_snapshot.snapshot_id,
                    prompt_id="application_readiness_rules_v2",
                    prompt_version="2.0.0",
                    result=report.model_dump(mode="json"),
                    evidence_used=evidence_used,
                    source_refs=source_refs,
                    dependency_hash=dependency.digest,
                    dependency_inputs=dependency.inputs,
                )
            )
            bundle = ApplicationAnalysisBundle(
                bundle_id=bundle_id,
                session_id=session_id,
                evidence_scope=evidence_scope,
                dependency_hash=dependency.digest,
                match_result=match_result,
                ats_result=ats_result,
                readiness_result=report,
                tailor_result=tailor_result,
                match_snapshot_id=match_snapshot.snapshot_id,
                ats_snapshot_id=ats_snapshot.snapshot_id,
                readiness_snapshot_id=readiness_snapshot.snapshot_id,
                tailor_snapshot_id=tailor_snapshot.snapshot_id,
            )
            self.repository.save_analysis_bundle(bundle)
            self.repository.save_report(report)
            suggestions = self._suggestions(session, master, report)
            self.repository.replace_pending_suggestions(session_id, suggestions)
            refreshed = self._session(session_id)
            completed = refreshed.model_copy(
                update={
                    "status": ApplicationLabStatus.REVIEW,
                    "current_step": 6,
                    "readiness_report_id": report.report_id,
                    "evidence_scope": evidence_scope,
                    "dependency_hash": dependency.digest,
                    "analysis_bundle_id": bundle.bundle_id,
                    "analysis_run_ids": [
                        *refreshed.analysis_run_ids,
                        match_snapshot.snapshot_id,
                        ats_snapshot.snapshot_id,
                        readiness_snapshot.snapshot_id,
                        tailor_snapshot.snapshot_id,
                    ],
                    "invalidated_steps": [step for step in refreshed.invalidated_steps if step < 5],
                    "warnings": list(dict.fromkeys([*refreshed.warnings, *context.warnings])),
                    "updated_at": utc_now(),
                }
            )
            self.repository.save_session(completed)
            return report, self.repository.list_suggestions(session_id), readiness_snapshot
        except Exception as exc:
            failed = self._session(session_id).model_copy(
                update={
                    "status": ApplicationLabStatus.FAILED,
                    "warnings": [
                        *session.warnings,
                        "A análise falhou sem alterar sugestões já revisadas.",
                    ],
                    "updated_at": utc_now(),
                }
            )
            self.repository.save_session(failed)
            raise ValueError(f"Não foi possível concluir a análise: {exc}") from exc

    def review_suggestion(
        self,
        session_id: str,
        suggestion_id: str,
        action: ReviewAction,
        *,
        edited_value: str = "",
    ) -> ApplicationSuggestion:
        """Apply a review decision without mutating any resume."""
        self._session(session_id)
        item = self.repository.get_suggestion(suggestion_id)
        if item is None or item.session_id != session_id:
            raise LookupError("Sugestão não encontrada nesta sessão.")
        if action == "edited" and not edited_value.strip():
            raise ValueError("Informe o texto revisado antes de aceitar a edição.")
        selected_text = edited_value if action == "edited" else item.after
        if action in {"accepted", "edited"} and selected_text.strip() and not item.evidence_used:
            raise ValueError("Afirmações sem evidência não podem ser aceitas.")
        reviewed = self.repository.review_suggestion(
            suggestion_id,
            SuggestionStatus(action),
            edited_value=edited_value.strip() if action == "edited" else "",
        )
        if reviewed is None:
            raise LookupError("Sugestão não encontrada.")
        return reviewed

    def create_variant(self, session_id: str, *, title: str = "") -> ResumeVariant:
        """Create a copy-on-write variant from explicitly accepted suggestions."""
        session = self._session(session_id)
        master = self._master(session.master_resume_id)
        job = self._job(session.job_snapshot_id)
        sections = deepcopy(master.sections)
        changes: list[ResumeVariantChange] = []
        warnings: list[str] = []
        for suggestion in self.repository.list_suggestions(session_id):
            if suggestion.status not in {SuggestionStatus.ACCEPTED, SuggestionStatus.EDITED}:
                continue
            after = (
                suggestion.edited_value
                if suggestion.status is SuggestionStatus.EDITED
                else suggestion.after
            ).strip()
            if not after:
                warnings.append(f"Sugestão {suggestion.suggestion_id} não contém texto aplicável.")
                continue
            applied = _replace_in_sections(sections, suggestion.before, after)
            if not applied:
                warnings.append(
                    f"Sugestão {suggestion.suggestion_id} preservada no diff, mas o texto-base mudou."
                )
            if not applied:
                continue
            changes.append(
                ResumeVariantChange(
                    change_type="edited" if suggestion.before else "added",
                    section=suggestion.section,
                    before=suggestion.before,
                    after=after,
                    reason=suggestion.reason,
                    evidence_used=suggestion.evidence_used,
                    source_refs=suggestion.source_refs,
                    warning=""
                    if applied
                    else "Texto-base não localizado; revisão manual necessária.",
                )
            )
        variant = ResumeVariant(
            resume_variant_id=session.resume_variant_id or uuid4().hex,
            master_resume_id=master.master_resume_id,
            job_snapshot_id=job.snapshot_id,
            title=title.strip() or f"{master.title} — {job.title or 'vaga'}",
            target_role=job.title,
            sections=sections,
            source_profile_item_ids=master.source_profile_item_ids,
            change_set=changes,
            validation_warnings=warnings,
        )
        saved = self.repository.save_variant(variant)
        self.repository.save_session(
            session.model_copy(
                update={
                    "resume_variant_id": saved.resume_variant_id,
                    "current_step": 8,
                    "invalidated_steps": [step for step in session.invalidated_steps if step < 7],
                    "updated_at": utc_now(),
                }
            )
        )
        return saved

    def create_kit(self, session_id: str) -> tuple[ApplicationKit, AnalysisSnapshot]:
        """Build an evidence-linked draft kit; every item still requires review."""
        session = self._session(session_id)
        master = self._master(session.master_resume_id)
        job = self._job(session.job_snapshot_id)
        variant = (
            self.repository.get_variant(session.resume_variant_id)
            if session.resume_variant_id
            else None
        )
        bundle = self.repository.get_analysis_bundle(session.analysis_bundle_id)
        if bundle is None:
            raise ValueError("Execute a análise antes de criar o Application Kit.")
        selected_refs = list(bundle.evidence_scope.get("selected_source_refs", []))
        selected_ids = list(bundle.evidence_scope.get("selected_evidence_ids", []))
        evidence: list[str | dict[str, Any]] = list(dict.fromkeys([*selected_refs, *selected_ids]))
        job_evidence: list[str | dict[str, Any]] = list(job.source_refs)
        safe_summary = bundle.tailor_result.professional_summary.strip()
        project_highlight = next(
            (item for item in bundle.tailor_result.improved_bullets if item.strip()), ""
        )
        evidence_warning = [] if evidence else ["Sem evidência confirmada selecionada."]
        items = [
            ApplicationKitItem(
                type="headline",
                content=job.title,
                evidence_used=job_evidence,
                warnings=["Headline baseada somente no título da oportunidade; revise."],
            ),
            ApplicationKitItem(
                type="professional_summary",
                content=safe_summary,
                evidence_used=evidence,
                warnings=evidence_warning,
            ),
            ApplicationKitItem(
                type="about_section",
                content=safe_summary,
                evidence_used=evidence,
                warnings=evidence_warning,
            ),
            ApplicationKitItem(
                type="recruiter_message",
                content=(
                    f"Olá, tenho interesse na oportunidade {job.title}. {safe_summary}".strip()
                    if safe_summary
                    else ""
                ),
                evidence_used=[*job_evidence, *evidence],
                warnings=evidence_warning,
            ),
            ApplicationKitItem(
                type="cover_letter",
                content=(
                    f"Tenho interesse em {job.title} na {job.organization}. {safe_summary}".strip()
                    if safe_summary
                    else ""
                ),
                evidence_used=[*job_evidence, *evidence],
                warnings=evidence_warning,
            ),
            ApplicationKitItem(
                type="why_this_role",
                content=(
                    f"A oportunidade busca {job.title}; a evidência selecionada registra: "
                    f"{safe_summary}"
                    if safe_summary
                    else ""
                ),
                evidence_used=[*job_evidence, *evidence],
                warnings=evidence_warning,
            ),
            ApplicationKitItem(
                type="project_highlight",
                content=project_highlight,
                evidence_used=evidence,
                warnings=evidence_warning,
            ),
            ApplicationKitItem(
                type="manual_checklist",
                content=(
                    "Revisar fatos; confirmar anexos; conferir destinatário; "
                    "registrar envio manual no Tracker."
                ),
                evidence_used=job_evidence,
                warnings=["Checklist não executa nem envia a candidatura."],
            ),
        ]
        existing = (
            self.repository.get_kit(session.application_kit_id)
            if session.application_kit_id
            else None
        )
        protected = {
            item.type: item
            for item in (existing.items if existing else [])
            if item.status.value in {"accepted", "edited", "rejected"}
        }
        items = [protected.get(item.type, item) for item in items]
        kit = ApplicationKit(
            application_kit_id=session.application_kit_id or uuid4().hex,
            session_id=session_id,
            items=items,
            warnings=["Nenhum item é enviado automaticamente."],
            dependency_hash=bundle.dependency_hash,
        )
        saved = self.repository.save_kit(kit)
        self._save_kit_assets(saved, session, master, job, bundle)
        resume_snapshot = self._resume_snapshot(variant or master)
        snapshot = self.snapshots.create_analysis(
            AnalysisSnapshot(
                analysis_type="application_kit",
                job_snapshot_id=job.snapshot_id,
                resume_snapshot_id=resume_snapshot.snapshot_id,
                prompt_id="application_kit_local_v1",
                prompt_version="1.0.0",
                result=saved.model_dump(mode="json"),
                evidence_used=[item for entry in saved.items for item in entry.evidence_used],
                source_refs=list(dict.fromkeys([*master.source_refs, *job.source_refs])),
                dependency_hash=bundle.dependency_hash,
            )
        )
        refreshed = self._session(session_id)
        self.repository.save_session(
            refreshed.model_copy(
                update={
                    "application_kit_id": saved.application_kit_id,
                    "current_step": 9,
                    "analysis_run_ids": [*refreshed.analysis_run_ids, snapshot.snapshot_id],
                    "updated_at": utc_now(),
                }
            )
        )
        return saved, snapshot

    def _save_kit_assets(
        self,
        kit: ApplicationKit,
        session: ApplicationLabSession,
        master: MasterResume,
        job: JobSnapshot,
        bundle: ApplicationAnalysisBundle,
    ) -> None:
        repository = ProfessionalAssetRepository(self.database_path)
        type_map = {
            "professional_summary": AssetType.PROFESSIONAL_BIO,
            "about_section": AssetType.ABOUT_SECTION,
            "recruiter_message": AssetType.RECRUITER_MESSAGE,
            "cover_letter": AssetType.COVER_LETTER,
            "project_highlight": AssetType.PROJECT_HIGHLIGHT,
        }
        source_refs = list(
            dict.fromkeys(
                [
                    *bundle.evidence_scope.get("selected_source_refs", []),
                    *job.source_refs,
                ]
            )
        )
        evidence_ids = list(bundle.evidence_scope.get("selected_evidence_ids", []))
        match_snapshot = self.snapshots.get_analysis(bundle.match_snapshot_id)
        document_snapshot_ids = (
            [match_snapshot.resume_snapshot_id]
            if match_snapshot is not None and match_snapshot.resume_snapshot_id
            else []
        )
        for item in kit.items:
            asset_type = type_map.get(item.type)
            if asset_type is None or not item.content.strip():
                continue
            repository.save(
                ProfessionalAsset(
                    asset_id=f"{kit.application_kit_id}:{item.type}",
                    asset_type=asset_type,
                    title=f"{item.type.replace('_', ' ').title()} — {job.title}",
                    status=AssetStatus.REVIEW,
                    content=item.content,
                    structured_content={"kit_item_id": item.item_id, "item_type": item.type},
                    profile_id=master.profile_id,
                    target_opportunity_id=job.opportunity_id,
                    application_lab_session_id=session.session_id,
                    evidence_scope_id=str(bundle.evidence_scope.get("scope_id", "")),
                    evidence_scope=bundle.evidence_scope,
                    source_refs=source_refs,
                    evidence_ids=evidence_ids,
                    document_snapshot_ids=document_snapshot_ids,
                    dependency_hash=bundle.dependency_hash,
                    review_status=EvidenceReviewStatus.SOURCED,
                )
            )
        repository.save(
            ProfessionalAsset(
                asset_id=kit.application_kit_id,
                asset_type=AssetType.APPLICATION_KIT,
                title=kit.title,
                status=AssetStatus.REVIEW,
                content="\n\n".join(item.content for item in kit.items if item.content.strip()),
                structured_content=kit.model_dump(mode="json"),
                profile_id=master.profile_id,
                target_opportunity_id=job.opportunity_id,
                application_lab_session_id=session.session_id,
                evidence_scope_id=str(bundle.evidence_scope.get("scope_id", "")),
                evidence_scope=bundle.evidence_scope,
                source_refs=source_refs,
                evidence_ids=evidence_ids,
                document_snapshot_ids=document_snapshot_ids,
                dependency_hash=bundle.dependency_hash,
                review_status=EvidenceReviewStatus.SOURCED,
            )
        )

    def review_kit_item(
        self,
        session_id: str,
        item_id: str,
        status: str,
        *,
        edited_content: str = "",
    ) -> ApplicationKitItem:
        session = self._session(session_id)
        if not session.application_kit_id:
            raise ValueError("Crie o Application Kit antes de revisar seus itens.")
        reviewed = self.repository.review_kit_item(
            session.application_kit_id,
            item_id,
            KitItemStatus(status),
            edited_content=edited_content,
        )
        if reviewed is None:
            raise LookupError("Item do Application Kit não encontrado.")
        return reviewed

    def export_kit(self, session_id: str) -> tuple[str, dict[str, str]]:
        session = self._session(session_id)
        kit = (
            self.repository.get_kit(session.application_kit_id)
            if session.application_kit_id
            else None
        )
        if kit is None:
            raise LookupError("Application Kit não encontrado.")
        return kit.application_kit_id, {
            item.type: (
                item.edited_content if item.status is KitItemStatus.EDITED else item.content
            )
            for item in kit.items
            if item.status in {KitItemStatus.ACCEPTED, KitItemStatus.EDITED}
        }

    def create_action_plan(
        self, session_id: str, *, period_days: Literal[7, 14, 30] = 7
    ) -> ApplicationActionPlan:
        session = self._session(session_id)
        report = self.repository.get_report(session_id=session_id)
        if report is None:
            raise ValueError("Execute a análise antes de criar o plano de ação.")
        gaps = report.top_blockers or report.recommended_edits
        now = utc_now()
        plan = ApplicationActionPlan(
            action_plan_id=session.action_plan_id or uuid4().hex,
            session_id=session_id,
            period_days=period_days,
            items=[
                ActionPlanItem(
                    title=gap,
                    reason="Gap priorizado pelo relatório determinístico de prontidão.",
                    priority="high" if index < 2 else "medium",
                    due_at=now
                    + timedelta(days=max(1, round(period_days * (index + 1) / max(1, len(gaps))))),
                    related_gap=gap,
                    related_evidence=report.evidence_used,
                    estimated_effort="30–60 min",
                )
                for index, gap in enumerate(gaps[:8])
            ],
        )
        saved = self.repository.save_action_plan(plan)
        refreshed = self._session(session_id)
        self.repository.save_session(
            refreshed.model_copy(
                update={
                    "action_plan_id": saved.action_plan_id,
                    "current_step": 10,
                    "updated_at": utc_now(),
                }
            )
        )
        return saved

    def save_to_tracker(
        self,
        session_id: str,
        *,
        privacy_acknowledged: bool,
        source_capture_id: str = "",
    ) -> str:
        """Save one deduplicated tracker card linked to all Lab artifacts and snapshots."""
        if not privacy_acknowledged:
            raise ValueError("Confirme o aviso de privacidade antes de salvar no Tracker.")
        session = self._session(session_id)
        report = self.repository.get_report(session_id=session_id)
        if report is None:
            raise ValueError("Execute a análise antes de salvar no Tracker.")
        master = self._master(session.master_resume_id)
        job = self._job(session.job_snapshot_id)
        variant = (
            self.repository.get_variant(session.resume_variant_id)
            if session.resume_variant_id
            else None
        )
        resume = variant or master
        resume_snapshot = self._resume_snapshot(resume)
        bundle = self.repository.get_analysis_bundle(session.analysis_bundle_id)
        if bundle is None:
            raise ValueError("Bundle de análise ausente; execute a análise novamente.")
        requirements = [item.requirement_text for item in bundle.match_result.requirements]
        analysis = match_result_to_job_analysis(bundle.match_result).model_copy(
            update={"ats_score": bundle.ats_result.ats_score}
        )
        operation = fingerprint_dependencies(
            profile=master.profile_id or "default",
            opportunity_identity=job.opportunity_id or job.content_hash,
            job_snapshot=job.snapshot_id,
            resume_snapshot=resume_snapshot.snapshot_id,
            application_lab_session=session_id,
            action_type="save_to_tracker",
        )
        now = utc_now()
        stored = StoredAnalysis(
            id=f"application-{operation.digest[:28]}",
            job_title=job.title,
            company=job.organization,
            modality=job.location,
            status=(JobStatus.GOOD_FIT if analysis.should_apply() else JobStatus.ANALYZED),
            analysis=analysis,
            notes="Criado pelo Application Lab; revisar antes de qualquer candidatura.",
            privacy_acknowledged=True,
            source_url=job.source_url,
            source_urls=list(job.source_refs),
            collection_method="browser_assisted_capture" if source_capture_id else "manual_url",
            requirements=requirements,
            source_capture_id=source_capture_id,
            job_snapshot_id=job.snapshot_id,
            resume_snapshot_id=resume_snapshot.snapshot_id,
            match_analysis_snapshot_id=bundle.match_snapshot_id,
            ats_analysis_snapshot_id=bundle.ats_snapshot_id,
            stage_history=[
                {
                    "status": (
                        JobStatus.GOOD_FIT.value
                        if analysis.should_apply()
                        else JobStatus.ANALYZED.value
                    ),
                    "at": now.isoformat(),
                }
            ],
            created_at=now,
            updated_at=now,
        )
        lab_snapshot_id = bundle.readiness_snapshot_id
        kit_snapshot_id = _kit_snapshot_id(session.analysis_run_ids, self.snapshots)
        application_payload = {
            **stored.model_dump(mode="json"),
            "application_lab": {
                "session_id": session_id,
                "readiness_score": report.readiness_score,
                "readiness_is_probability": False,
                "match_score": bundle.match_result.score_breakdown.match_score,
                "ats_score": bundle.ats_result.ats_score,
                "opportunity_fit_score": (
                    bundle.match_result.score_breakdown.opportunity_fit_score
                ),
                "confidence_score": bundle.match_result.score_breakdown.confidence_score,
                "risk_score": bundle.match_result.score_breakdown.risk_score,
            },
        }
        application = self.applications.complete_lab_transaction(
            ApplicationRecord(
                id=stored.id,
                job_snapshot_id=job.snapshot_id,
                resume_snapshot_id=resume_snapshot.snapshot_id,
                match_analysis_snapshot_id=bundle.match_snapshot_id,
                ats_analysis_snapshot_id=bundle.ats_snapshot_id,
                source_capture_id=source_capture_id,
                job_title=job.title,
                organization=job.organization,
                source_url=job.source_url,
                status=stored.status.value,
                stage_history=stored.stage_history,
                application_lab_session_id=session_id,
                readiness_report_id=report.report_id,
                resume_variant_id=session.resume_variant_id,
                application_kit_id=session.application_kit_id,
                action_plan_id=session.action_plan_id,
                lab_analysis_snapshot_id=lab_snapshot_id,
                readiness_analysis_snapshot_id=bundle.readiness_snapshot_id,
                tailor_analysis_snapshot_id=bundle.tailor_snapshot_id,
                analysis_bundle_id=bundle.bundle_id,
                application_kit_snapshot_id=kit_snapshot_id,
                dependency_hash=bundle.dependency_hash,
                payload=application_payload,
                created_at=now,
                updated_at=now,
            ),
            session_id=session_id,
            idempotency_key=operation.digest,
        )
        return application.id

    def _resume_snapshot(
        self,
        resume: MasterResume | ResumeVariant,
        *,
        dependency_hash: str = "",
        evidence_scope: dict[str, Any] | None = None,
    ) -> ResumeSnapshot:
        return self.snapshots.create_resume(
            ResumeSnapshot(
                profile_id=(resume.profile_id if isinstance(resume, MasterResume) else ""),
                master_resume_id=resume.master_resume_id,
                resume_variant_id=(
                    resume.resume_variant_id if isinstance(resume, ResumeVariant) else ""
                ),
                document_kind="variant" if isinstance(resume, ResumeVariant) else "master",
                title=resume.title,
                content=resume_plain_text(resume),
                structured_sections={
                    "sections": [item.model_dump(mode="json") for item in resume.sections]
                },
                source_profile_item_ids=resume.source_profile_item_ids,
                dependency_hash=dependency_hash,
                evidence_scope=evidence_scope or {},
            )
        )

    def _suggestions(
        self,
        session: ApplicationLabSession,
        master: MasterResume,
        report: ApplicationReadinessReport,
    ) -> list[ApplicationSuggestion]:
        existing = self.repository.list_suggestions(session.session_id)
        protected = [
            item
            for item in existing
            if item.status in {SuggestionStatus.ACCEPTED, SuggestionStatus.EDITED}
        ]
        allowed_refs = set(session.selected_context_refs)
        generated: list[ApplicationSuggestion] = []
        for section in master.sections:
            for entry in section.entries:
                refs = entry.source_refs
                if not entry.enabled or not entry.confirmed_by_user or not refs:
                    continue
                if allowed_refs and not allowed_refs.intersection(refs):
                    continue
                if (
                    entry.title
                    and entry.content
                    and entry.title.casefold() not in entry.content.casefold()
                ):
                    suggestion_evidence: list[str | dict[str, Any]] = list(refs)
                    generated.append(
                        ApplicationSuggestion(
                            session_id=session.session_id,
                            suggestion_type="bullet",
                            section=section.title,
                            before=entry.content,
                            after=f"{entry.title}: {entry.content}",
                            reason="Tornar a evidência confirmada mais explícita sem acrescentar fatos.",
                            evidence_used=suggestion_evidence,
                            source_refs=refs,
                        )
                    )
                if len(generated) >= 5:
                    break
            if len(generated) >= 5:
                break
        generated.extend(
            ApplicationSuggestion(
                session_id=session.session_id,
                suggestion_type="coverage",
                section="Prontidão",
                reason=item,
                warnings=["Requer texto e evidência confirmados pelo usuário."],
            )
            for item in report.recommended_edits[:5]
        )
        protected_keys = {(item.section, item.before, item.after) for item in protected}
        return [
            *protected,
            *[
                item
                for item in generated
                if (item.section, item.before, item.after) not in protected_keys
            ],
        ]

    def _session(self, session_id: str) -> ApplicationLabSession:
        session = self.repository.get_session(session_id)
        if session is None:
            raise LookupError("Sessão do Application Lab não encontrada.")
        return session

    def _master(self, master_resume_id: str) -> MasterResume:
        if not master_resume_id:
            raise ValueError("Selecione um Currículo Mestre.")
        resume = self.repository.get_master_resume(master_resume_id)
        if resume is None:
            raise LookupError("Currículo Mestre não encontrado.")
        return resume

    def _job(self, snapshot_id: str) -> JobSnapshot:
        if not snapshot_id:
            raise ValueError("Selecione uma vaga antes de continuar.")
        snapshot = self.snapshots.get_job(snapshot_id)
        if snapshot is None:
            raise LookupError("Snapshot da vaga não encontrado.")
        return snapshot


def _replace_in_sections(sections: list[Any], before: str, after: str) -> bool:
    if not before:
        return False
    for section in sections:
        if before in section.content:
            section.content = section.content.replace(before, after, 1)
            section.updated_at = utc_now()
            return True
        for entry in section.entries:
            if before in entry.content:
                entry.content = entry.content.replace(before, after, 1)
                entry.updated_at = utc_now()
                return True
    return False


def _job_requirements(data: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for key in ("requirements", "required_skills", "mandatory_requirements", "qualifications"):
        value = data.get(key)
        if isinstance(value, list):
            for item in value:
                text = (
                    item
                    if isinstance(item, str)
                    else str(item.get("name", ""))
                    if isinstance(item, dict)
                    else ""
                )
                if text.strip():
                    result.append(text.strip())
    return list(dict.fromkeys(result))


def _kit_snapshot_id(snapshot_ids: list[str], snapshots: SnapshotStore) -> str:
    for snapshot_id in reversed(snapshot_ids):
        snapshot = snapshots.get_analysis(snapshot_id)
        if snapshot is not None and snapshot.analysis_type == "application_kit":
            return snapshot.snapshot_id
    return ""


__all__ = ["ApplicationLabService", "ReviewAction"]
