"""FastAPI service adapters for Universal Career Profile endpoints."""

from __future__ import annotations

from fastapi import HTTPException
from modules.academic import LattesImportInput, LattesService
from modules.ai.prompt_loader import default_prompt_registry
from modules.profile import ProfileContextOrchestrator
from modules.profile.models import ProfileImportDraft, ProfileItem
from modules.profile.service import UniversalCareerProfileService

from apps.api.schemas.profile import (
    ProfileContextResponse,
    ProfileDeduplicateResponse,
    ProfileImportTextRequest,
    ProfileImportTextResponse,
    ProfileItemPatchRequest,
    ProfileItemRequest,
    ProfileItemResponse,
    ProfileLattesConfirmRequest,
    ProfileLattesConfirmResponse,
    ProfileLattesImportRequest,
    ProfileLattesImportResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from apps.api.services.ai_settings import get_ai_runtime


def profile_get() -> ProfileResponse:
    """Return the active universal profile."""
    return ProfileResponse(profile=UniversalCareerProfileService().get_profile())


def profile_update(request: ProfileUpdateRequest) -> ProfileResponse:
    """Update top-level profile metadata."""
    data = request.model_dump(exclude={"request_id"})
    profile = UniversalCareerProfileService().update_profile(data)
    return ProfileResponse(profile=profile, message="Perfil atualizado.")


def profile_add_item(request: ProfileItemRequest) -> ProfileItemResponse:
    """Add one reviewed profile item."""
    item = ProfileItem.model_validate(
        {
            **request.model_dump(exclude={"request_id"}),
            "confirmed_by_user": True,
            "confidence": "high",
        }
    )
    saved = UniversalCareerProfileService().add_item(item, confirmed_by_user=True)
    return ProfileItemResponse(item=saved, message="Item adicionado ao perfil.")


def profile_patch_item(item_id: str, request: ProfileItemPatchRequest) -> ProfileItemResponse:
    """Patch one item and mark it confirmed by the user."""
    updates = request.model_dump(exclude={"request_id"}, exclude_unset=True)
    try:
        item = UniversalCareerProfileService().patch_item(item_id, updates)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProfileItemResponse(item=item, message="Item atualizado.")


def profile_delete_item(item_id: str) -> ProfileResponse:
    """Remove one item from the local profile."""
    try:
        profile = UniversalCareerProfileService().delete_item(item_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProfileResponse(profile=profile, message="Item removido do perfil.")


def profile_import_text(
    request: ProfileImportTextRequest,
) -> tuple[ProfileImportTextResponse, list[str]]:
    """Extract profile item drafts from text with optional AI."""
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Cole um texto para importar.")

    service = UniversalCareerProfileService()
    local = service.import_text_local(
        request.text,
        source_type=request.source_type,
        warnings=[],
    )
    if not request.use_ai:
        return ProfileImportTextResponse.model_validate(local.model_dump()), local.warnings

    runtime = get_ai_runtime("profile")
    warnings = list(runtime.warnings)
    if not runtime.use_ai or runtime.provider_name == "local":
        fallback = service.import_text_local(
            request.text,
            source_type=request.source_type,
            warnings=[*warnings, "IA indisponivel; usei extração local do perfil."],
        )
        return ProfileImportTextResponse.model_validate(fallback.model_dump()), fallback.warnings

    payload: dict[str, object] = {
        "text": request.text,
        "source_type": request.source_type,
        "language": request.language,
    }
    if _contains_secret_field(payload):
        raise HTTPException(status_code=422, detail="Payload contem campo inseguro.")

    try:
        spec = default_prompt_registry().get("profile_items_extractor_v1")
        output = runtime.provider.generate_structured(spec, payload)
        draft = ProfileImportDraft.model_validate(output)
        draft = draft.model_copy(
            update={
                "provider_used": runtime.provider_name,
                "requested_provider": str(runtime.requested_provider),
                "analysis_mode": "ai",
                "needs_user_review": True,
                "items": [
                    item.model_copy(
                        update={
                            "source": item.source or request.source_type,
                            "confirmed_by_user": False,
                        }
                    )
                    for item in draft.items
                ],
                "warnings": [
                    *warnings,
                    *draft.warnings,
                    "Itens sugeridos pela IA exigem revisão antes de entrar no perfil.",
                ],
            }
        )
        return ProfileImportTextResponse.model_validate(draft.model_dump()), draft.warnings
    except Exception:
        fallback = service.import_text_local(
            request.text,
            source_type=request.source_type,
            warnings=[*warnings, "IA falhou; usei extração local do perfil."],
        )
        fallback = fallback.model_copy(
            update={
                "requested_provider": str(runtime.requested_provider),
                "analysis_mode": "fallback",
            }
        )
        return ProfileImportTextResponse.model_validate(fallback.model_dump()), fallback.warnings


def profile_import_lattes(
    request: ProfileLattesImportRequest,
) -> tuple[ProfileLattesImportResponse, list[str]]:
    """Extract Lattes and academic ProfileItem drafts without saving them."""
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Cole um texto do Lattes para importar.")
    payload = LattesImportInput.model_validate(request.model_dump(exclude={"request_id"}))
    if _contains_secret_field(payload.model_dump()):
        raise HTTPException(status_code=422, detail="Payload contém campo inseguro.")

    service = LattesService()
    if not request.use_ai:
        local = service.draft_local(payload)
        return ProfileLattesImportResponse.model_validate(local.model_dump()), local.warnings

    runtime = get_ai_runtime("lattes")
    warnings = list(runtime.warnings)
    if not runtime.use_ai or runtime.provider_name == "local":
        fallback = service.draft_local(
            payload,
            warnings=[*warnings, "IA indisponível; usei parser local de Lattes."],
        )
        return ProfileLattesImportResponse.model_validate(fallback.model_dump()), fallback.warnings

    result = service.draft_with_ai(
        payload,
        provider=runtime.provider,
        prompt_registry=default_prompt_registry(),
        provider_name=runtime.provider_name,
        requested_provider=str(runtime.requested_provider),
        warnings=warnings,
    )
    return ProfileLattesImportResponse.model_validate(result.model_dump()), result.warnings


def profile_confirm_lattes(
    request: ProfileLattesConfirmRequest,
) -> ProfileLattesConfirmResponse:
    """Save explicitly selected academic items into the Universal Career Profile."""
    if not request.items:
        raise HTTPException(status_code=422, detail="Selecione ao menos um item para confirmar.")
    result = LattesService().confirm_items(request.items)
    return ProfileLattesConfirmResponse.model_validate(result.model_dump())


def profile_deduplicate() -> ProfileDeduplicateResponse:
    """Return duplicate suggestions without destructive merge."""
    suggestions = UniversalCareerProfileService().deduplicate()
    return ProfileDeduplicateResponse(
        suggestions=suggestions,
        message=f"{len(suggestions)} sugestao(oes) de duplicidade encontrada(s).",
    )


def profile_context() -> ProfileContextResponse:
    """Return the profile context used by AI-assisted workflows."""
    context = ProfileContextOrchestrator().build_context(purpose="profile_api")
    return ProfileContextResponse(
        context=context,
        message="Contexto do Perfil Profissional montado localmente.",
    )


def _contains_secret_field(value: object) -> bool:
    secret_markers = {"api_key", "apikey", "secret", "token", "cookie", "session"}
    if isinstance(value, dict):
        for key, nested in value.items():
            if any(marker in str(key).lower() for marker in secret_markers):
                return True
            if _contains_secret_field(nested):
                return True
    if isinstance(value, list):
        return any(_contains_secret_field(item) for item in value)
    return False
