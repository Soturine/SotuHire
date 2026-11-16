"""FastAPI adapter for the guided application domain service."""

from __future__ import annotations

import base64
import binascii
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import HTTPException
from modules.application_lab.export import prepare_resume_export
from modules.application_lab.ingestion_service import ResumeIngestionService
from modules.application_lab.models import (
    ApplicationLabSession,
    MasterResume,
    ResumeVariant,
)
from modules.application_lab.profile_projection import (
    SECTION_LAYOUT,
    apply_profile_updates,
    master_resume_from_profile,
    profile_changes,
    profile_updates,
    refresh_profile_facts,
)
from modules.application_lab.repository import StaleWriteError
from modules.application_lab.service import ApplicationLabService
from modules.profile.json_resume import section_for_item
from modules.profile.service import UniversalCareerProfileService

from apps.api.schemas.application_lab import (
    ApplicationLabAnalyzeResponse,
    ApplicationLabSessionCreateRequest,
    ApplicationLabSessionDetail,
    ApplicationLabSessionPage,
    MasterResumeResponse,
    PaginationMeta,
    ProfileChangedItem,
    ProfileFieldChange,
    ProfileUpdateItem,
    ProfileUpdatesResponse,
    ResumeExportResponse,
    ResumeIngestionResponse,
    ResumeTemplatesResponse,
    ResumeVariantPage,
    ResumeVariantResponse,
)

ANALYSIS_PROGRESS = [
    "Extraindo currículo",
    "Carregando evidências",
    "Estruturando vaga",
    "Comparando requisitos",
    "Validando afirmações",
    "Gerando sugestões",
    "Criando variante",
    "Salvando snapshots",
]


class ApplicationLabApiService:
    def __init__(self, domain: ApplicationLabService | None = None) -> None:
        self.domain = domain or ApplicationLabService()
        self.repository = self.domain.repository

    def create_session(
        self, request: ApplicationLabSessionCreateRequest
    ) -> ApplicationLabSessionDetail:
        session = self._call(
            self.domain.create_session,
            ApplicationLabSession(
                profile_id=request.profile_id,
                master_resume_id=request.master_resume_id,
                job_id=request.job_id,
                job_snapshot_id=request.job_snapshot_id,
                selected_context_refs=request.selected_context_refs,
            ),
        )
        return self.detail(session.session_id)

    def list_sessions(self, *, limit: int, offset: int) -> ApplicationLabSessionPage:
        bounded_limit, bounded_offset = _page(limit, offset)
        items = self.repository.list_sessions(limit=bounded_limit, offset=bounded_offset)
        total = self.repository.count_sessions()
        return ApplicationLabSessionPage(
            items=items,
            pagination=PaginationMeta(
                limit=bounded_limit,
                offset=bounded_offset,
                total=total,
                has_more=bounded_offset + len(items) < total,
            ),
        )

    def detail(self, session_id: str) -> ApplicationLabSessionDetail:
        session = self.repository.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Sessão do Application Lab não encontrada.")
        return ApplicationLabSessionDetail(
            session=session,
            analysis_bundle=(
                self.repository.get_analysis_bundle(session.analysis_bundle_id)
                if session.analysis_bundle_id
                else None
            ),
            report=self.repository.get_report(session_id=session_id),
            suggestions=self.repository.list_suggestions(session_id),
            variant=(
                self.repository.get_variant(session.resume_variant_id)
                if session.resume_variant_id
                else None
            ),
            kit=(
                self.repository.get_kit(session.application_kit_id)
                if session.application_kit_id
                else None
            ),
            action_plan=(
                self.repository.get_action_plan(session.action_plan_id)
                if session.action_plan_id
                else None
            ),
        )

    def update_session(
        self, session_id: str, changes: dict[str, Any]
    ) -> ApplicationLabSessionDetail:
        self._call(self.domain.update_session, session_id, changes)
        return self.detail(session_id)

    def cancel_session(self, session_id: str) -> ApplicationLabSessionDetail:
        self._call(self.domain.cancel_session, session_id)
        return self.detail(session_id)

    def analyze(self, session_id: str) -> ApplicationLabAnalyzeResponse:
        _, _, snapshot = self._call(self.domain.analyze, session_id)
        detail = self.detail(session_id)
        bundle = detail.analysis_bundle
        return ApplicationLabAnalyzeResponse(
            **detail.model_dump(),
            analysis_snapshot_id=snapshot.snapshot_id,
            analysis_snapshot_ids=(
                {
                    "match": bundle.match_snapshot_id,
                    "ats": bundle.ats_snapshot_id,
                    "readiness": bundle.readiness_snapshot_id,
                    "tailor": bundle.tailor_snapshot_id,
                }
                if bundle is not None
                else {}
            ),
            progress_steps=ANALYSIS_PROGRESS,
        )

    def master(self) -> MasterResumeResponse:
        resume = self.repository.get_master_resume()
        if resume is None:
            raise HTTPException(status_code=404, detail="Currículo Mestre ainda não foi criado.")
        return MasterResumeResponse(resume=resume)

    def master_from_profile(self) -> MasterResumeResponse:
        """Create the Master Resume from confirmed profile facts instead of a second import."""
        if self.repository.get_master_resume() is not None:
            raise HTTPException(
                status_code=409,
                detail="Currículo Mestre já existe; use as atualizações do Perfil para trazer itens novos.",
            )
        profile = UniversalCareerProfileService().get_profile()
        resume = master_resume_from_profile(profile)
        if not resume.sections:
            raise HTTPException(
                status_code=422,
                detail="O Perfil ainda não tem itens confirmados para montar o Currículo Mestre.",
            )
        return MasterResumeResponse(resume=self._call(self.repository.save_master_resume, resume))

    def profile_updates(self) -> ProfileUpdatesResponse:
        master = self.master().resume
        profile = UniversalCareerProfileService().get_profile()
        layout = {source: title for source, _section_type, title in SECTION_LAYOUT}
        return ProfileUpdatesResponse(
            master_resume_id=master.master_resume_id,
            items=[
                ProfileUpdateItem(
                    item_id=item.item_id,
                    item_type=item.type,
                    title=item.title,
                    subtitle=item.organization or item.institution or "",
                    section_title=layout[section_for_item(item)],
                )
                for item in profile_updates(profile, master)
            ],
            changed=[
                ProfileChangedItem(
                    item_id=item.item_id,
                    item_type=item.type,
                    title=item.title,
                    section_title=section_title,
                    changes=[
                        ProfileFieldChange(field=field, in_master=before, in_profile=after)
                        for field, (before, after) in diff.items()
                    ],
                )
                for item, section_title, diff in profile_changes(profile, master)
            ],
        )

    def refresh_profile_facts(self, item_ids: list[str]) -> MasterResumeResponse:
        """Bring the current Profile text of chosen facts into the Master (never the reverse)."""
        master = self.master().resume
        profile = UniversalCareerProfileService().get_profile()
        try:
            updated = refresh_profile_facts(master, profile, item_ids)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if updated is master:
            return MasterResumeResponse(resume=master)
        return MasterResumeResponse(
            resume=self._call(
                self.repository.save_master_resume, updated, expected_updated_at=master.updated_at
            )
        )

    def apply_profile_updates(self, item_ids: list[str]) -> MasterResumeResponse:
        master = self.master().resume
        profile = UniversalCareerProfileService().get_profile()
        try:
            updated = apply_profile_updates(master, profile, item_ids)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if updated is master:  # every chosen fact is already there: a retry, nothing to write
            return MasterResumeResponse(resume=master)
        return MasterResumeResponse(
            resume=self._call(
                self.repository.save_master_resume, updated, expected_updated_at=master.updated_at
            )
        )

    def save_master(
        self,
        resume: MasterResume,
        *,
        expected_updated_at: datetime | None = None,
        replace_existing: bool = False,
    ) -> MasterResumeResponse:
        """Save a Master Resume.

        A client that edits a copy it loaded sends that copy's ``updated_at`` as
        ``expected_updated_at`` and gets 409 instead of erasing a newer save (another tab, or
        facts applied from the Profile meanwhile).

        A different resume (an imported draft has its own id) becomes the Master the app uses
        only with ``replace_existing``: before, adopting a re-imported file silently took the
        place of the Master being edited. With it, ``expected_updated_at`` must name the Master
        the person saw being replaced. The previous one is not deleted; it stays in the database
        and in backups, no longer the current Master.
        """
        current = self.repository.get_master_resume()
        if current is not None and current.master_resume_id != resume.master_resume_id:
            if not replace_existing:
                raise HTTPException(
                    status_code=409,
                    detail="Já existe um Currículo Mestre; confirme a substituição para adotar "
                    "este currículo no lugar dele.",
                )
            if expected_updated_at is not None and current.updated_at != expected_updated_at:
                raise HTTPException(
                    status_code=409,
                    detail="O Currículo Mestre mudou depois de ser exibido; revise de novo "
                    "antes de substituí-lo.",
                )
            expected_updated_at = None  # checked above; the new resume has no stored copy yet
        prepared = resume.model_copy(update={"updated_at": datetime.now(UTC)})
        return MasterResumeResponse(
            resume=self._call(
                self.repository.save_master_resume,
                prepared,
                expected_updated_at=expected_updated_at,
            )
        )

    def ingest_resume(self, file_name: str, content_base64: str) -> ResumeIngestionResponse:
        try:
            content = base64.b64decode(content_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Conteúdo base64 inválido.") from exc
        document, draft = self._call(
            ResumeIngestionService(self.domain.database_path).ingest,
            file_name,
            content,
        )
        return ResumeIngestionResponse(document=document, master_resume_draft=draft)

    def variants(self, *, master_resume_id: str, limit: int, offset: int) -> ResumeVariantPage:
        bounded_limit, bounded_offset = _page(limit, offset)
        items = self.repository.list_variants(
            master_resume_id=master_resume_id,
            limit=bounded_limit,
            offset=bounded_offset,
        )
        total = self.repository.count_variants(master_resume_id=master_resume_id)
        return ResumeVariantPage(
            items=items,
            pagination=PaginationMeta(
                limit=bounded_limit,
                offset=bounded_offset,
                total=total,
                has_more=bounded_offset + len(items) < total,
            ),
        )

    def save_variant(
        self, variant: ResumeVariant, *, expected_updated_at: datetime | None = None
    ) -> ResumeVariantResponse:
        if self.repository.get_master_resume(variant.master_resume_id) is None:
            raise HTTPException(status_code=404, detail="Currículo Mestre não encontrado.")
        prepared = variant.model_copy(update={"updated_at": datetime.now(UTC)})
        return ResumeVariantResponse(
            variant=self._call(
                self.repository.save_variant, prepared, expected_updated_at=expected_updated_at
            )
        )

    def variant(self, variant_id: str) -> ResumeVariantResponse:
        variant = self.repository.get_variant(variant_id)
        if variant is None:
            raise HTTPException(status_code=404, detail="Variante não encontrada.")
        return ResumeVariantResponse(variant=variant)

    def update_variant(
        self,
        variant_id: str,
        changes: dict[str, Any],
        *,
        expected_updated_at: datetime | None = None,
    ) -> ResumeVariantResponse:
        """Patch a variant. With ``expected_updated_at`` a newer stored copy answers 409."""
        current = self.variant(variant_id).variant
        allowed = {"title", "target_role", "sections", "validation_warnings"}
        update = {
            key: value for key, value in changes.items() if key in allowed and value is not None
        }
        update["updated_at"] = datetime.now(UTC)
        return self.save_variant(
            current.model_copy(update=update), expected_updated_at=expected_updated_at
        )

    def templates(self) -> ResumeTemplatesResponse:
        return ResumeTemplatesResponse(items=self.repository.list_templates())

    def export_variant(
        self,
        variant_id: str,
        *,
        export_format: str,
        template_id: str,
        page_size: Literal["A4", "Letter"] = "A4",
    ) -> ResumeExportResponse:
        variant = self.variant(variant_id).variant
        if template_id not in {item.template_id for item in self.repository.list_templates()}:
            raise HTTPException(status_code=422, detail="Template de currículo desconhecido.")
        export, payload = self._call(
            prepare_resume_export,
            variant,
            export_format=export_format,
            template_id=template_id,
            page_size=page_size,
        )
        self._call(self.repository.save_export, export)
        return ResumeExportResponse(export=export, payload=payload)

    @staticmethod
    def _call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except StaleWriteError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc


def get_application_lab_api_service() -> ApplicationLabApiService:
    return ApplicationLabApiService()


def _page(limit: int, offset: int) -> tuple[int, int]:
    return max(1, min(limit, 200)), max(0, offset)


__all__ = ["ApplicationLabApiService", "get_application_lab_api_service"]
