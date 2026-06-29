"""Job Radar API service adapters."""

from __future__ import annotations

import json

from fastapi import HTTPException
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.schemas.analysis_insights import RadarMatchExplanationOutput, WishlistDraftOutput
from modules.profile import ProfileContext, ProfileContextOrchestrator
from modules.radar import JobRadarService, JobWishlist, RadarResult, RadarSource
from modules.radar.wishlist_draft import build_local_wishlist_draft
from pydantic import ValidationError

from apps.api.schemas.radar import (
    RadarAlertPatchRequest,
    RadarAlertResponse,
    RadarAlertsResponse,
    RadarResultPatchRequest,
    RadarResultResponse,
    RadarResultsResponse,
    RadarRunRequest,
    RadarRunResponse,
    RadarRunsResponse,
    RadarSaveInboxResponse,
    RadarSaveTrackerResponse,
    RadarSourcePatchRequest,
    RadarSourceRequest,
    RadarSourceResponse,
    RadarSourcesResponse,
    RadarStatsResponse,
    RadarWishlistDraftRequest,
    RadarWishlistDraftResponse,
    RadarWishlistPatchRequest,
    RadarWishlistRequest,
    RadarWishlistResponse,
    RadarWishlistsResponse,
)
from apps.api.services.ai_settings import get_ai_runtime


def radar_wishlists() -> RadarWishlistsResponse:
    """List radar wishlists."""
    return RadarWishlistsResponse(wishlists=JobRadarService().list_wishlists())


def radar_create_wishlist(request: RadarWishlistRequest) -> RadarWishlistResponse:
    """Create one wishlist."""
    wishlist = JobRadarService().create_wishlist(
        JobWishlist.model_validate(request.model_dump(exclude={"request_id"}))
    )
    return RadarWishlistResponse(wishlist=wishlist, message="Wishlist criada.")


def radar_draft_wishlist(
    request: RadarWishlistDraftRequest,
) -> tuple[RadarWishlistDraftResponse, list[str]]:
    """Create an unsaved wishlist draft from free text and optional profile context."""
    if not request.free_text.strip():
        raise HTTPException(status_code=422, detail="Informe o que voce esta buscando.")
    context = _draft_profile_context(request)
    local_draft = build_local_wishlist_draft(
        request.free_text,
        profile_context=context if request.use_profile_context else None,
    )
    runtime = get_ai_runtime("radar")
    warnings = [*runtime.warnings]

    if not runtime.use_ai or runtime.provider_name == "local":
        draft = local_draft.model_copy(
            update={
                "provider_used": runtime.provider_name,
                "analysis_mode": runtime.analysis_mode,
                "warnings": [*local_draft.warnings, *warnings],
                "needs_user_review": True,
            }
        )
        return RadarWishlistDraftResponse.model_validate(draft.model_dump()), warnings

    payload = {
        "free_text": request.free_text,
        "profile_context": context.model_dump(mode="json") if context else {},
        "language": request.language,
    }
    if _contains_secret_field(payload):
        raise HTTPException(status_code=422, detail="Payload de IA contem campo inseguro.")

    try:
        spec = default_prompt_registry().get("job_wishlist_builder_v1")
        output = runtime.provider.generate_structured(spec, payload)
        ai_draft = WishlistDraftOutput.model_validate(output)
        ai_draft = ai_draft.model_copy(
            update={
                "provider_used": runtime.provider_name,
                "analysis_mode": "ai",
                "needs_user_review": True,
                "warnings": [
                    *warnings,
                    *ai_draft.warnings,
                    "Revise manualmente antes de salvar a wishlist.",
                ],
            }
        )
        return RadarWishlistDraftResponse.model_validate(ai_draft.model_dump()), warnings
    except (RuntimeError, ValidationError, ValueError, TypeError) as exc:
        fallback = build_local_wishlist_draft(
            request.free_text,
            profile_context=context if request.use_profile_context else None,
            provider_used="local",
            analysis_mode="fallback",
            warnings=[
                *warnings,
                "IA indisponivel ou resposta invalida; usei rascunho local.",
                str(exc)[:160],
            ],
        )
        return RadarWishlistDraftResponse.model_validate(fallback.model_dump()), warnings


def radar_patch_wishlist(
    wishlist_id: str,
    request: RadarWishlistPatchRequest,
) -> RadarWishlistResponse:
    """Patch one wishlist."""
    try:
        wishlist = JobRadarService().update_wishlist(
            wishlist_id,
            request.model_dump(exclude={"request_id"}, exclude_unset=True),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarWishlistResponse(wishlist=wishlist, message="Wishlist atualizada.")


def radar_delete_wishlist(wishlist_id: str) -> RadarWishlistResponse:
    """Deactivate one wishlist."""
    try:
        wishlist = JobRadarService().delete_wishlist(wishlist_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarWishlistResponse(wishlist=wishlist, message="Wishlist desativada.")


def radar_sources() -> RadarSourcesResponse:
    """List radar sources and documented adapters."""
    service = JobRadarService()
    return RadarSourcesResponse(sources=service.list_sources(), adapters=service.adapters())


def radar_create_source(request: RadarSourceRequest) -> RadarSourceResponse:
    """Create one radar source."""
    source = JobRadarService().create_source(
        RadarSource.model_validate(request.model_dump(exclude={"request_id"}))
    )
    return RadarSourceResponse(source=source, message="Fonte do Radar criada.")


def radar_patch_source(source_id: str, request: RadarSourcePatchRequest) -> RadarSourceResponse:
    """Patch one radar source."""
    try:
        source = JobRadarService().update_source(
            source_id,
            request.model_dump(exclude={"request_id"}, exclude_unset=True),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarSourceResponse(source=source, message="Fonte do Radar atualizada.")


def radar_delete_source(source_id: str) -> RadarSourceResponse:
    """Disable one radar source."""
    try:
        source = JobRadarService().delete_source(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarSourceResponse(source=source, message="Fonte do Radar desativada.")


def radar_run(request: RadarRunRequest) -> tuple[RadarRunResponse, list[str]]:
    """Execute one manual Job Radar run."""
    ai_enricher = _radar_ai_enricher if request.use_ai else None
    try:
        run, results, alerts, warnings = JobRadarService().run(
            source_ids=request.source_ids,
            wishlist_id=request.wishlist_id,
            resume_text=request.resume_text,
            keywords=request.keywords,
            use_ai=request.use_ai,
            ai_enricher=ai_enricher,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return (
        RadarRunResponse(
            run=run,
            results=results,
            alerts=alerts,
            message=(
                f"Radar concluido: {run.total_found} vaga(s), "
                f"{run.total_alerted} alerta(s), {run.total_errors} erro(s)."
            ),
        ),
        warnings,
    )


def radar_runs() -> RadarRunsResponse:
    """List radar runs."""
    return RadarRunsResponse(runs=JobRadarService().list_runs())


def radar_results(status: str = "", source_id: str = "") -> RadarResultsResponse:
    """List radar results."""
    return RadarResultsResponse(
        results=JobRadarService().list_results(status=status, source_id=source_id)
    )


def radar_patch_result(result_id: str, request: RadarResultPatchRequest) -> RadarResultResponse:
    """Patch one radar result."""
    try:
        result = JobRadarService().update_result(result_id, status=request.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarResultResponse(result=result, message="Resultado atualizado.")


def radar_save_inbox(result_id: str) -> RadarSaveInboxResponse:
    """Save one radar result to source inbox."""
    try:
        inbox_item, result = JobRadarService().save_result_to_inbox(result_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarSaveInboxResponse(
        result=result,
        inbox_item=inbox_item,
        message="Resultado salvo na Caixa de Entrada.",
    )


def radar_save_tracker(result_id: str) -> RadarSaveTrackerResponse:
    """Save one radar result directly to tracker."""
    try:
        tracker_id, result = JobRadarService().save_result_to_tracker(result_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarSaveTrackerResponse(
        result=result,
        tracker_id=tracker_id,
        message="Resultado salvo em Candidaturas.",
    )


def radar_alerts(unread_only: bool = False) -> RadarAlertsResponse:
    """List local radar alerts."""
    return RadarAlertsResponse(alerts=JobRadarService().list_alerts(unread_only=unread_only))


def radar_patch_alert(alert_id: str, request: RadarAlertPatchRequest) -> RadarAlertResponse:
    """Patch one radar alert."""
    try:
        alert = JobRadarService().update_alert(alert_id, status=request.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarAlertResponse(alert=alert, message="Alerta atualizado.")


def radar_stats() -> RadarStatsResponse:
    """Return radar dashboard stats."""
    return RadarStatsResponse.model_validate(JobRadarService().stats().model_dump())


def _radar_ai_enricher(result: RadarResult, wishlist: JobWishlist) -> dict[str, object]:
    """Generate optional AI explanation for one radar match."""
    runtime = get_ai_runtime("radar")
    if not runtime.use_ai or runtime.provider_name == "local":
        raise RuntimeError("; ".join(runtime.warnings) or "IA indisponivel para Radar.")
    spec = default_prompt_registry().get("job_radar_match_explanation_v1")
    payload = {
        "job": {
            "title": result.title,
            "company": result.company,
            "description": result.description,
            "source": result.source_name,
            "url": result.url,
        },
        "wishlist": wishlist.model_dump(mode="json"),
        "local_match": {
            "radar_score": result.radar_score,
            "match_score": result.match_score,
            "ats_score": result.ats_score,
            "reasons": result.reasons,
            "evidence": result.evidence,
            "gaps": result.gaps,
        },
        "language": "pt-BR",
    }
    if "api_key" in json.dumps(payload).lower():
        raise RuntimeError("Payload de IA contem campo inseguro.")
    output = runtime.provider.generate_structured(spec, payload)
    enrichment = RadarMatchExplanationOutput.model_validate(output)
    return {
        **enrichment.model_dump(),
        "provider_used": runtime.provider_name,
        "warnings": [*runtime.warnings, *enrichment.warnings],
    }


def _draft_profile_context(request: RadarWishlistDraftRequest) -> ProfileContext | None:
    if not request.use_profile_context:
        return None
    try:
        return ProfileContextOrchestrator().build_context(
            purpose="job_radar_wishlist",
            override=request.profile_context_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _contains_secret_field(value: object) -> bool:
    secret_markers = {"api_key", "apikey", "secret", "token", "cookie", "session"}
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = str(key).lower()
            if any(marker in normalized_key for marker in secret_markers):
                return True
            if _contains_secret_field(nested):
                return True
    if isinstance(value, list):
        return any(_contains_secret_field(item) for item in value)
    return False
