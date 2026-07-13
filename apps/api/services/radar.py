"""Job Radar API service adapters."""

from __future__ import annotations

import json

from fastapi import HTTPException
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.schemas.analysis_insights import RadarMatchExplanationOutput, WishlistDraftOutput
from modules.context import (
    CareerContext,
    CareerContextEngine,
    CareerContextPurpose,
    context_brief,
    format_context_for_prompt,
)
from modules.radar import (
    JobRadarService,
    JobWishlist,
    LocalNotificationService,
    RadarResult,
    RadarSchedule,
    RadarSchedulerRuntime,
    RadarScheduleStore,
    RadarSource,
    ScheduledRadarService,
)
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
    RadarScheduledRunResponse,
    RadarScheduledRunsResponse,
    RadarSchedulePatchRequest,
    RadarScheduleRequest,
    RadarScheduleResponse,
    RadarSchedulerStatusResponse,
    RadarSchedulesResponse,
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

_scheduler_runtime: RadarSchedulerRuntime | None = None


def _runtime() -> RadarSchedulerRuntime:
    """Return a runtime bound to the current local data directory."""
    global _scheduler_runtime
    expected_path = RadarScheduleStore().path
    if _scheduler_runtime is None or _scheduler_runtime.service.store.path != expected_path:
        _scheduler_runtime = RadarSchedulerRuntime(
            ScheduledRadarService(store=RadarScheduleStore())
        )
    return _scheduler_runtime


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
    context = _draft_career_context(request)
    local_draft = build_local_wishlist_draft(
        request.free_text,
        profile_context=context if request.use_profile_context else None,
    )
    runtime = get_ai_runtime("radar")
    warnings = [*runtime.warnings, *(context.warnings if context else [])]

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
        "profile_context": _context_payload(context, include_sensitive=False),
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
    career_context = _safe_context(
        CareerContextPurpose.RADAR,
        query=" ".join([request.resume_text, " ".join(request.keywords)]),
    )
    context_text = format_context_for_prompt(
        career_context,
        include_sensitive=False,
        confirmed_only=True,
    )
    resume_text = "\n\n".join(part for part in [request.resume_text.strip(), context_text] if part)
    try:
        run, results, alerts, warnings = JobRadarService().run(
            source_ids=request.source_ids,
            wishlist_id=request.wishlist_id,
            resume_text=resume_text,
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
        [*warnings, *career_context.warnings],
    )


def radar_runs() -> RadarRunsResponse:
    """List radar runs."""
    return RadarRunsResponse(runs=JobRadarService().list_runs())


def radar_schedules() -> RadarSchedulesResponse:
    """List local Radar schedules."""
    return RadarSchedulesResponse(schedules=ScheduledRadarService().list_schedules())


def radar_get_schedule(schedule_id: str) -> RadarScheduleResponse:
    """Return one local Radar schedule."""
    try:
        schedule = ScheduledRadarService().get_schedule(schedule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarScheduleResponse(schedule=schedule)


def radar_create_schedule(request: RadarScheduleRequest) -> RadarScheduleResponse:
    """Create one local Radar schedule."""
    schedule = ScheduledRadarService().create_schedule(
        RadarSchedule.model_validate(request.model_dump(exclude={"request_id"}))
    )
    return RadarScheduleResponse(schedule=schedule, message="Agendamento criado.")


def radar_patch_schedule(
    schedule_id: str,
    request: RadarSchedulePatchRequest,
) -> RadarScheduleResponse:
    """Patch one local Radar schedule."""
    try:
        schedule = ScheduledRadarService().update_schedule(
            schedule_id,
            request.model_dump(exclude={"request_id"}, exclude_unset=True),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarScheduleResponse(schedule=schedule, message="Agendamento atualizado.")


def radar_delete_schedule(schedule_id: str) -> RadarScheduleResponse:
    """Disable one local Radar schedule."""
    try:
        schedule = ScheduledRadarService().delete_schedule(schedule_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RadarScheduleResponse(schedule=schedule, message="Agendamento pausado.")


def radar_run_schedule_now(schedule_id: str) -> RadarScheduledRunResponse:
    """Execute one schedule manually."""
    try:
        scheduled_run = ScheduledRadarService().run_schedule(
            schedule_id,
            manual=True,
            ai_enricher=_radar_ai_enricher,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    notifications = LocalNotificationService().list_notifications()
    return RadarScheduledRunResponse(
        scheduled_run=scheduled_run,
        notifications=notifications[:5],
        message="Agendamento executado para revisao manual.",
    )


def radar_scheduled_runs() -> RadarScheduledRunsResponse:
    """List scheduled run history."""
    return RadarScheduledRunsResponse(scheduled_runs=ScheduledRadarService().list_scheduled_runs())


def radar_scheduler_status() -> RadarSchedulerStatusResponse:
    """Return scheduler runtime status."""
    return RadarSchedulerStatusResponse.model_validate(_runtime().status().model_dump())


def radar_scheduler_start() -> RadarSchedulerStatusResponse:
    """Start local in-process scheduler."""
    return RadarSchedulerStatusResponse.model_validate(
        _runtime().start(ai_enricher=_radar_ai_enricher).model_dump()
    )


def radar_scheduler_stop() -> RadarSchedulerStatusResponse:
    """Stop local in-process scheduler."""
    return RadarSchedulerStatusResponse.model_validate(_runtime().stop().model_dump())


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
    career_context = _safe_context(
        CareerContextPurpose.RADAR,
        query=" ".join([result.title, result.company, result.description]),
    )
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
        "career_context": (
            _context_payload(career_context, include_sensitive=False)
            if runtime.allow_memory_context
            else {
                "shared_with_provider": False,
                "summary": context_brief(career_context),
            }
        ),
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


def _draft_career_context(request: RadarWishlistDraftRequest) -> CareerContext | None:
    if not request.use_profile_context:
        return None
    try:
        return CareerContextEngine().build(
            CareerContextPurpose.WISHLIST,
            query=request.free_text,
            profile_context_override=request.profile_context_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _safe_context(purpose: CareerContextPurpose, *, query: str = "") -> CareerContext:
    return CareerContextEngine().build(purpose, query=query, max_evidence=10)


def _context_payload(
    context: CareerContext | None,
    *,
    include_sensitive: bool,
) -> dict[str, object]:
    if context is None:
        return {}
    return {
        "purpose": context.purpose.value,
        "summary": context_brief(context),
        "goals": context.goals[:8],
        "domains": context.domains[:8],
        "seniority": context.seniority[:6],
        "locations": context.locations[:8],
        "work_models": context.work_models[:6],
        "contract_types": context.contract_types[:6],
        "constraints": context.constraints[:8],
        "evidence": [
            item.model_dump(mode="json")
            for item in context.evidence
            if include_sensitive or not item.sensitive
        ][:10],
        "warnings": context.warnings,
        "privacy_notes": context.privacy_notes,
    }


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
