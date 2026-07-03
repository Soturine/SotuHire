"""FastAPI service adapters for public exam endpoints."""

from __future__ import annotations

from fastapi import HTTPException
from modules.ai.prompt_loader import default_prompt_registry
from modules.public_exams import PublicExamImportInput, PublicExamService

from apps.api.schemas.public_exams import (
    PublicExamAnalyzeRequest,
    PublicExamAnalyzeResponse,
    PublicExamConfirmRequest,
    PublicExamConfirmResponse,
    PublicExamImportRequest,
    PublicExamImportResponse,
    PublicExamListResponse,
    PublicExamStudyPlanRequest,
    PublicExamStudyPlanResponse,
)
from apps.api.services.ai_settings import get_ai_runtime


def public_exams_import(
    request: PublicExamImportRequest,
) -> tuple[PublicExamImportResponse, list[str]]:
    """Extract a public exam draft without saving it."""
    payload = PublicExamImportInput.model_validate(request.model_dump(exclude={"request_id"}))
    if _contains_secret_field(payload.model_dump()):
        raise HTTPException(status_code=422, detail="Payload contém campo inseguro.")
    service = PublicExamService()
    if not request.use_ai:
        local = service.draft_local(payload)
        return PublicExamImportResponse.model_validate(local.model_dump()), local.warnings

    runtime = get_ai_runtime("public_exams")
    warnings = list(runtime.warnings)
    if not runtime.use_ai or runtime.provider_name == "local":
        fallback = service.draft_local(
            payload,
            warnings=[*warnings, "IA indisponível; usei parser local de edital."],
        )
        return PublicExamImportResponse.model_validate(fallback.model_dump()), fallback.warnings

    result = service.draft_with_ai(
        payload,
        provider=runtime.provider,
        prompt_registry=default_prompt_registry(),
        provider_name=runtime.provider_name,
        requested_provider=str(runtime.requested_provider),
        warnings=warnings,
    )
    return PublicExamImportResponse.model_validate(result.model_dump()), result.warnings


def public_exams_list(query: str = "") -> PublicExamListResponse:
    """List saved public exam notices."""
    return PublicExamListResponse.model_validate(
        PublicExamService().list_notices(query).model_dump()
    )


def public_exams_get(notice_id: str):
    """Return one notice or raise 404."""
    notice = PublicExamService().get_notice(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Edital não encontrado.")
    return notice


def public_exams_delete(notice_id: str) -> PublicExamListResponse:
    """Delete one saved notice."""
    deleted = PublicExamService().delete_notice(notice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Edital não encontrado.")
    return public_exams_list()


def public_exams_confirm(
    notice_id: str,
    request: PublicExamConfirmRequest,
) -> PublicExamConfirmResponse:
    """Save a reviewed notice."""
    notice = request.notice.model_copy(update={"notice_id": notice_id or request.notice.notice_id})
    result = PublicExamService().confirm_notice(notice)
    return PublicExamConfirmResponse.model_validate(result.model_dump())


def public_exams_analyze(
    notice_id: str,
    request: PublicExamAnalyzeRequest,
) -> PublicExamAnalyzeResponse:
    """Compare a saved notice with the Universal Career Profile."""
    try:
        result = PublicExamService().analyze_notice(notice_id, role_id=request.role_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PublicExamAnalyzeResponse.model_validate(result.model_dump())


def public_exams_study_plan(
    notice_id: str,
    request: PublicExamStudyPlanRequest,
) -> PublicExamStudyPlanResponse:
    """Generate an initial study plan."""
    try:
        result = PublicExamService().study_plan(
            notice_id,
            role_id=request.role_id,
            weekly_hours=request.weekly_hours,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PublicExamStudyPlanResponse.model_validate(result.model_dump())


def _contains_secret_field(value: object) -> bool:
    secret_markers = {"api_key", "apikey", "secret", "token", "cookie", "session", "headers"}
    if isinstance(value, dict):
        for key, nested in value.items():
            if any(marker in str(key).lower() for marker in secret_markers):
                return True
            if _contains_secret_field(nested):
                return True
    if isinstance(value, list):
        return any(_contains_secret_field(item) for item in value)
    return False
