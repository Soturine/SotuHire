"""Service layer for public exam notice imports, scoring and study plans."""

from __future__ import annotations

from collections.abc import Iterable

from modules.ai.prompt_registry import PromptRegistry
from modules.ai.providers import AIProvider
from modules.context import CareerContextEngine, CareerContextPurpose, context_brief
from modules.profile.service import UniversalCareerProfileService

from .formatters import checklist_from_requirements
from .models import (
    ExamNotice,
    ExamRole,
    PublicExamAnalyzeResult,
    PublicExamConfirmResult,
    PublicExamImportInput,
    PublicExamImportResult,
    PublicExamListResult,
    PublicExamStudyPlanResult,
)
from .parser import OFFICIAL_NOTICE_WARNING, parse_public_exam_notice
from .scoring import score_exam_fit
from .store import PublicExamStore
from .study_plan import build_study_plan


class PublicExamService:
    """Application service for the public exams foundation."""

    def __init__(
        self,
        *,
        store: PublicExamStore | None = None,
        profile_service: UniversalCareerProfileService | None = None,
        context_engine: CareerContextEngine | None = None,
    ) -> None:
        self.store = store or PublicExamStore()
        self.profile_service = profile_service or UniversalCareerProfileService()
        self.context_engine = context_engine or CareerContextEngine()

    def draft_local(
        self,
        payload: PublicExamImportInput,
        *,
        warnings: Iterable[str] = (),
    ) -> PublicExamImportResult:
        """Parse a pasted edital locally without saving it."""
        result = parse_public_exam_notice(payload)
        if not warnings:
            return result
        combined = [*warnings, *result.warnings]
        notice = result.notice.model_copy(update={"warnings": combined})
        return result.model_copy(update={"notice": notice, "warnings": combined})

    def draft_with_ai(
        self,
        payload: PublicExamImportInput,
        *,
        provider: AIProvider,
        prompt_registry: PromptRegistry,
        provider_name: str,
        requested_provider: str,
        warnings: Iterable[str] = (),
    ) -> PublicExamImportResult:
        """Use optional AI as an extractor, falling back locally on any issue."""
        local = self.draft_local(payload, warnings=warnings)
        try:
            spec = prompt_registry.get("public_exam_notice_extractor_v1")
            output = provider.generate_structured(
                spec,
                {
                    "text": payload.text,
                    "source_url": payload.source_url,
                    "source_name": payload.source_name,
                    "language": payload.language,
                    "local_parser_draft": local.model_dump(mode="json"),
                },
            )
            draft = PublicExamImportResult.model_validate(output)
            if not _has_useful_ai_notice(draft):
                raise ValueError("AI public exam draft did not include useful notice fields.")
            notice = _normalize_notice(draft.notice, payload)
            roles = [
                role.model_copy(update={"notice_id": notice.notice_id})
                for role in (draft.roles or notice.roles)
            ]
            notice = notice.model_copy(
                update={
                    "roles": roles,
                    "timeline": draft.timeline or notice.timeline,
                    "subjects": draft.subjects or notice.subjects,
                    "general_requirements": draft.requirements or notice.general_requirements,
                    "warnings": [
                        *warnings,
                        *draft.warnings,
                        OFFICIAL_NOTICE_WARNING,
                        "Rascunho estruturado por IA: revise todos os campos antes de salvar.",
                    ],
                    "status": "draft",
                }
            )
            return draft.model_copy(
                update={
                    "notice": notice,
                    "roles": roles,
                    "timeline": notice.timeline,
                    "subjects": notice.subjects,
                    "requirements": notice.general_requirements,
                    "warnings": notice.warnings,
                    "needs_user_review": True,
                    "provider_used": provider_name,
                    "requested_provider": requested_provider,
                    "analysis_mode": "ai",
                }
            )
        except Exception:
            return local.model_copy(
                update={
                    "warnings": [
                        *local.warnings,
                        "IA indisponível ou resposta inválida; usei parser local de edital.",
                    ],
                    "requested_provider": requested_provider,
                    "analysis_mode": "fallback",
                }
            )

    def list_notices(self, query: str = "") -> PublicExamListResult:
        """List persisted notices."""
        notices = self.store.search_notices(query) if query else self.store.list_notices()
        return PublicExamListResult(notices=notices)

    def get_notice(self, notice_id: str) -> ExamNotice | None:
        """Return one persisted notice."""
        return self.store.get_notice(notice_id)

    def delete_notice(self, notice_id: str) -> bool:
        """Delete one persisted notice."""
        return self.store.delete_notice(notice_id)

    def confirm_notice(self, notice: ExamNotice) -> PublicExamConfirmResult:
        """Persist a reviewed edital; drafts are not auto-saved."""
        saved = self.store.save_notice(notice)
        return PublicExamConfirmResult(
            notice=saved,
            message="Edital revisado salvo localmente. Nenhuma inscrição foi feita.",
        )

    def analyze_notice(self, notice_id: str, *, role_id: str = "") -> PublicExamAnalyzeResult:
        """Compare one saved notice/role with the Universal Career Profile."""
        notice = self._notice_or_raise(notice_id)
        role = _select_role(notice, role_id)
        profile = self.profile_service.get_profile()
        query = " ".join(
            [
                notice.title,
                notice.organization,
                role.title if role else "",
                role.required_degree if role else "",
                role.required_registry if role else "",
            ]
        )
        context = self.context_engine.build(
            CareerContextPurpose.PUBLIC_EXAMS,
            query=query,
            include_memory=True,
            include_tracker=True,
            include_sources=True,
            include_extension=True,
            include_github=True,
            max_evidence=16,
        )
        fit = score_exam_fit(notice, role, profile, context)
        checklist = checklist_from_requirements(
            [*fit.missing_requirements, *fit.uncertain_requirements, *fit.matched_requirements]
        )
        return PublicExamAnalyzeResult(
            notice=notice,
            role=role,
            fit_score=fit,
            context_summary=context_brief(context),
            checklist=checklist,
            warnings=[*notice.warnings, *fit.warnings],
        )

    def study_plan(
        self,
        notice_id: str,
        *,
        role_id: str = "",
        weekly_hours: int = 8,
    ) -> PublicExamStudyPlanResult:
        """Generate a small initial study plan draft."""
        notice = self._notice_or_raise(notice_id)
        role = _select_role(notice, role_id)
        plan = build_study_plan(notice, role, weekly_hours=weekly_hours)
        return PublicExamStudyPlanResult(
            notice=notice,
            role=role,
            study_plan=plan,
            warnings=plan.warnings,
        )

    def _notice_or_raise(self, notice_id: str) -> ExamNotice:
        notice = self.store.get_notice(notice_id)
        if notice is None:
            raise KeyError("Edital não encontrado.")
        return notice


def _normalize_notice(notice: ExamNotice, payload: PublicExamImportInput) -> ExamNotice:
    return notice.model_copy(
        update={
            "raw_text": notice.raw_text or payload.text,
            "source_url": notice.source_url or payload.source_url,
            "source_name": notice.source_name or payload.source_name,
            "status": "draft",
            "opportunity_type": notice.opportunity_type or "public_exam",
        }
    )


def _has_useful_ai_notice(draft: PublicExamImportResult) -> bool:
    notice = draft.notice
    roles = draft.roles or notice.roles
    return bool(
        notice.title.strip()
        or notice.organization.strip()
        or notice.exam_board.strip()
        or roles
        or draft.requirements
        or draft.subjects
        or notice.timeline.exam_date
        or notice.timeline.registration_end
    )


def _select_role(notice: ExamNotice, role_id: str = "") -> ExamRole | None:
    if role_id:
        return next((role for role in notice.roles if role.role_id == role_id), None)
    return notice.roles[0] if notice.roles else None
