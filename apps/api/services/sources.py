"""Source collection service adapters for frontend API routes."""

from __future__ import annotations

import json

from fastapi import HTTPException
from modules.scraping.browser_session import inspect_browser_session, launch_authenticated_browser
from modules.scraping.collection import collect_authenticated_source
from modules.scraping.schemas import ScrapingSource
from modules.sources.imports import SourceImportService

from apps.api.schemas.sources import (
    AuthenticatedBrowserCollectRequest,
    AuthenticatedBrowserCollectResponse,
    AuthenticatedBrowserLaunchRequest,
    AuthenticatedBrowserOpportunityItem,
    AuthenticatedBrowserStatusResponse,
    SourceCaptureImportJobResponse,
    SourceCapturePatchRequest,
    SourceCaptureResponse,
    SourceCaptureSaveTrackerResponse,
    SourceCapturesResponse,
    SourceDedupeResponse,
    SourceImportCsvRequest,
    SourceImportJsonRequest,
    SourceImportResponse,
    SourceImportsResponse,
    SourceImportTextRequest,
    SourceImportUrlRequest,
    SourceStatsResponse,
)


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


def source_imports() -> SourceImportsResponse:
    """List the persistent opportunity inbox."""
    items, batches = SourceImportService().list_imports()
    return SourceImportsResponse(items=items, batches=batches)


def source_import_text(request: SourceImportTextRequest) -> tuple[SourceImportResponse, list[str]]:
    """Import a pasted job into the source inbox."""
    try:
        batch, items, warnings = SourceImportService().import_text(
            text=request.text,
            url=request.url,
            company=request.company,
            title=request.title,
            source_name=request.source_name,
            notes=request.notes,
            use_ai=request.use_ai,
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


def source_stats() -> SourceStatsResponse:
    """Return source stats."""
    return SourceStatsResponse.model_validate(SourceImportService().stats())
