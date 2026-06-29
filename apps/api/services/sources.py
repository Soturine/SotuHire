"""Source collection service adapters for frontend API routes."""

from __future__ import annotations

import json

from fastapi import HTTPException
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.schemas.analysis_insights import SourceImportEnrichmentOutput
from modules.profile import ProfileContextOrchestrator
from modules.scraping.browser_session import inspect_browser_session, launch_authenticated_browser
from modules.scraping.collection import collect_authenticated_source
from modules.scraping.schemas import ScrapingSource
from modules.sources.imports import SourceImportAiContext, SourceImportService

from apps.api.schemas.sources import (
    AuthenticatedAssistedCaptureRequest,
    AuthenticatedAssistedCaptureResponse,
    AuthenticatedBrowserCollectRequest,
    AuthenticatedBrowserCollectResponse,
    AuthenticatedBrowserLaunchRequest,
    AuthenticatedBrowserOpportunityItem,
    AuthenticatedBrowserStatusResponse,
    SourceCaptureImportJobResponse,
    SourceCaptureMergeRequest,
    SourceCapturePatchRequest,
    SourceCaptureResponse,
    SourceCaptureSaveTrackerResponse,
    SourceCapturesResponse,
    SourceDedupeResponse,
    SourceDirectoryResponse,
    SourceExportRequest,
    SourceExportResponse,
    SourceImportCsvRequest,
    SourceImportJsonRequest,
    SourceImportResponse,
    SourceImportsResponse,
    SourceImportTextRequest,
    SourceImportUrlRequest,
    SourceStatsResponse,
)
from apps.api.services.ai_settings import get_ai_runtime


def authenticated_browser_status(endpoint: str) -> AuthenticatedBrowserStatusResponse:
    """Return the status of the local authenticated browser session."""
    status = inspect_browser_session(endpoint)
    return AuthenticatedBrowserStatusResponse(
        available=status.available,
        endpoint=status.endpoint,
        browser=status.browser,
        message=status.message,
    )


def authenticated_browser_launch(
    request: AuthenticatedBrowserLaunchRequest,
) -> AuthenticatedBrowserStatusResponse:
    """Open or reuse the dedicated browser for manual login."""
    try:
        status = launch_authenticated_browser(request.start_url, request.browser_cdp_url)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AuthenticatedBrowserStatusResponse(
        available=status.available,
        endpoint=status.endpoint,
        browser=status.browser,
        message=status.message,
    )


def authenticated_browser_collect(
    request: AuthenticatedBrowserCollectRequest,
) -> AuthenticatedBrowserCollectResponse:
    """Collect opportunities through the existing authorized browser connector."""
    if not request.authorized_use:
        raise HTTPException(
            status_code=422,
            detail="Confirme que o uso da fonte autenticada esta autorizado antes de coletar.",
        )

    source = ScrapingSource(
        name=request.name,
        type="authenticated_browser",
        url=request.url,
        collection_mode="AUTHENTICATED_BROWSER",
        enabled=True,
        max_items=request.max_items,
        max_pages=request.max_pages,
        delay_seconds=request.delay_seconds,
        browser_cdp_url=request.browser_cdp_url,
        authorized_use=request.authorized_use,
        authorization_reference=request.authorization_reference,
    )
    result = collect_authenticated_source(source)
    return AuthenticatedBrowserCollectResponse(
        new_count=result.new_count,
        duplicate_count=result.duplicate_count,
        updated_count=result.updated_count,
        failures=result.failures,
        opportunities=[
            AuthenticatedBrowserOpportunityItem(
                title=opportunity.title,
                company=opportunity.company or "",
                source_url=opportunity.source_url,
                confidence=opportunity.confidence,
            )
            for opportunity in result.opportunities
        ],
    )


def authenticated_assisted_capture(
    request: AuthenticatedAssistedCaptureRequest,
) -> AuthenticatedAssistedCaptureResponse:
    """Save visible authenticated page text for user review without secrets."""
    if not request.user_review_required:
        raise HTTPException(status_code=422, detail="Captura assistida exige revisao humana.")
    if _contains_secret_field(request.metadata):
        raise HTTPException(
            status_code=422,
            detail="Metadata de captura nao pode conter cookies, tokens, sessao ou segredos.",
        )
    capture_text = (request.selected_text or "").strip() or request.visible_text.strip()
    if not capture_text:
        raise HTTPException(status_code=422, detail="Envie texto visivel para revisar.")

    profile_signals = _safe_profile_capture_signals(capture_text)
    capture = SourceImportService().import_authenticated_assisted_capture(
        visible_text=request.visible_text,
        selected_text=request.selected_text or "",
        source_url=request.source_url,
        source_host=request.source_host,
        capture_mode=request.capture_mode,
        metadata={
            "captured_at": request.captured_at,
            "profile_signals": profile_signals,
            "review_before_save": True,
        },
    )
    return AuthenticatedAssistedCaptureResponse(
        capture=capture,
        message="Captura assistida salva na Caixa de Entrada para revisao.",
    )


def source_imports() -> SourceImportsResponse:
    """List the persistent opportunity inbox."""
    items, batches = SourceImportService().list_imports()
    return SourceImportsResponse(items=items, batches=batches)


def source_import_text(request: SourceImportTextRequest) -> tuple[SourceImportResponse, list[str]]:
    """Import a pasted job into the source inbox."""
    try:
        ai_context = _source_ai_context(
            enabled=request.use_ai,
            text=request.text,
            source_url=request.url,
        )
        batch, items, warnings = SourceImportService().import_text(
            text=request.text,
            url=request.url,
            company=request.company,
            title=request.title,
            source_name=request.source_name,
            notes=request.notes,
            use_ai=request.use_ai,
            ai_context=ai_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return (
        SourceImportResponse(
            batch=batch,
            items=items,
            message=f"Importacao concluida: {batch.imported} item(ns), {batch.duplicates} duplicado(s).",
        ),
        warnings,
    )


def source_import_url(request: SourceImportUrlRequest) -> tuple[SourceImportResponse, list[str]]:
    """Import a public URL or return a safe manual-copy warning."""
    batch, items, warnings = SourceImportService().import_url(
        url=request.url,
        source_name=request.source_name,
        notes=request.notes,
        use_ai=request.use_ai,
        ai_context=_source_ai_context(enabled=request.use_ai, text="", source_url=request.url),
    )
    return (
        SourceImportResponse(
            batch=batch,
            items=items,
            message=(
                "Link importado para a Caixa de Entrada."
                if not warnings
                else "A URL foi registrada com aviso para revisao manual."
            ),
        ),
        warnings,
    )


def source_import_csv(request: SourceImportCsvRequest) -> tuple[SourceImportResponse, list[str]]:
    """Import CSV rows."""
    try:
        batch, items, warnings = SourceImportService().import_csv(
            csv_text=request.csv_text,
            source_name=request.source_name,
            use_ai=request.use_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return (
        SourceImportResponse(
            batch=batch,
            items=items,
            message=f"Importacao concluida: {batch.imported} itens, {batch.duplicates} duplicados, {batch.errors} erros.",
        ),
        warnings,
    )


def source_import_json(request: SourceImportJsonRequest) -> tuple[SourceImportResponse, list[str]]:
    """Import JSON rows."""
    entries = request.items
    if request.json_text.strip():
        try:
            loaded = json.loads(request.json_text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="JSON invalido.") from exc
        if not isinstance(loaded, list) or not all(isinstance(item, dict) for item in loaded):
            raise HTTPException(status_code=422, detail="JSON deve ser uma lista de objetos.")
        entries = loaded
    if not entries:
        raise HTTPException(status_code=422, detail="Envie items ou json_text.")
    batch, items, warnings = SourceImportService().import_json(
        entries=entries,
        source_name=request.source_name,
        use_ai=request.use_ai,
    )
    return (
        SourceImportResponse(
            batch=batch,
            items=items,
            message=f"Importacao concluida: {batch.imported} itens, {batch.duplicates} duplicados, {batch.errors} erros.",
        ),
        warnings,
    )


def source_captures() -> SourceCapturesResponse:
    """List persistent source captures."""
    return SourceCapturesResponse(captures=SourceImportService().list_captures())


def source_capture_patch(
    capture_id: str, request: SourceCapturePatchRequest
) -> SourceCaptureResponse:
    """Update one source capture."""
    try:
        capture = SourceImportService().patch_capture(
            capture_id,
            status=request.status,
            notes=request.notes,
            duplicate_of=request.duplicate_of,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SourceCaptureResponse(capture=capture, message="Captura atualizada.")


def source_capture_merge(
    capture_id: str, request: SourceCaptureMergeRequest
) -> SourceCaptureResponse:
    """Merge one duplicate into an existing record while preserving history."""
    try:
        capture = SourceImportService().merge_duplicate(
            capture_id,
            duplicate_of=request.duplicate_of,
            notes=request.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SourceCaptureResponse(
        capture=capture, message="Duplicata mesclada com histórico preservado."
    )


def source_capture_import_job(capture_id: str) -> SourceCaptureImportJobResponse:
    """Import one capture into the Vaga flow."""
    try:
        capture, job = SourceImportService().import_capture_to_job(capture_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SourceCaptureImportJobResponse(
        capture=capture,
        job=job,
        message="Item importado para Vaga.",
    )


def source_capture_save_tracker(capture_id: str) -> SourceCaptureSaveTrackerResponse:
    """Save one capture into tracker."""
    try:
        capture, tracker_id = SourceImportService().save_capture_to_tracker(capture_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SourceCaptureSaveTrackerResponse(
        capture=capture,
        tracker_id=tracker_id,
        message="Item salvo em Candidaturas.",
    )


def source_dedupe() -> SourceDedupeResponse:
    """Run local dedupe."""
    return SourceDedupeResponse(duplicates=SourceImportService().dedupe())


def source_directory(query: str = "") -> SourceDirectoryResponse:
    """Return safe source discovery directory entries."""
    result = SourceImportService().source_directory(query=query)
    return SourceDirectoryResponse(
        sources=result.sources,
        query=result.query,
        warnings=result.warnings,
    )


def source_export(request: SourceExportRequest) -> SourceExportResponse:
    """Export source inbox items without secrets."""
    result = SourceImportService().export_items(
        export_format=request.format,
        item_ids=request.item_ids,
    )
    return SourceExportResponse.model_validate(result.model_dump())


def source_stats() -> SourceStatsResponse:
    """Return source stats."""
    return SourceStatsResponse.model_validate(SourceImportService().stats())


def _source_ai_context(*, enabled: bool, text: str, source_url: str) -> SourceImportAiContext:
    """Build optional safe AI enrichment context for source imports."""
    if not enabled:
        return SourceImportAiContext()

    runtime = get_ai_runtime("source_import")
    warnings = list(runtime.warnings)
    if runtime.use_ai and runtime.provider_name != "local":
        try:
            spec = default_prompt_registry().get("source_import_enrichment_v1")
            output = runtime.provider.generate_structured(
                spec,
                {
                    "job_text": text,
                    "source_url": source_url,
                    "language": "pt-BR",
                },
            )
            enrichment = SourceImportEnrichmentOutput.model_validate(output)
            return SourceImportAiContext(
                requested=True,
                provider_used=runtime.provider_name,
                requested_provider=str(runtime.requested_provider),
                analysis_mode=runtime.analysis_mode,
                model=runtime.model,
                tags=enrichment.tags,
                domain=enrichment.domain,
                seniority=enrichment.seniority,
                priority=enrichment.priority,
                summary=enrichment.summary,
                duplicate_explanation=enrichment.duplicate_explanation,
                inconsistency_alerts=enrichment.inconsistency_alerts,
                warnings=[*warnings, *enrichment.warnings],
            )
        except Exception:
            warnings.append("IA falhou na importação; usei enriquecimento local.")
    elif not warnings:
        warnings.append("IA de importação indisponível ou local; usei extração local.")

    return SourceImportAiContext(
        requested=True,
        provider_used="local",
        requested_provider=str(runtime.requested_provider),
        analysis_mode="fallback" if runtime.requested_provider != "local" else "local",
        model="local",
        warnings=warnings,
    )


def _safe_profile_capture_signals(text: str) -> dict[str, object]:
    """Classify a capture with local profile context without inventing facts."""
    try:
        context = ProfileContextOrchestrator().build_context(purpose="authenticated_capture")
    except Exception:
        return {"profile_context_available": False}
    lowered = text.casefold()
    confirmed_titles = [
        item.title
        for item in [
            *context.skills,
            *context.certifications_and_registries,
            *context.education,
            *context.experiences,
        ]
        if item.confirmed_by_user and item.title.casefold() in lowered
    ][:10]
    gaps = [
        registry
        for registry in [
            "COREN",
            "OAB",
            "CRM",
            "CRP",
            "CREA",
            "CRQ",
            "CFT",
            "CRC",
            "CAU",
            "CREF",
            "CRF",
            "CRMV",
            "CRESS",
            "CRN",
            "CRO",
        ]
        if registry.casefold() in lowered
        and registry.casefold()
        not in {item.title.casefold() for item in context.certifications_and_registries}
    ][:10]
    return {
        "profile_context_available": True,
        "matched_confirmed_items": confirmed_titles,
        "possible_gaps": gaps,
        "confidence": "low" if not confirmed_titles else "medium",
    }


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
