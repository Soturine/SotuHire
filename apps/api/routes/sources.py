"""Source collection endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from modules.scraping.browser_session import DEFAULT_CDP_URL

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.sources import (
    AuthenticatedBrowserCollectRequest,
    AuthenticatedBrowserCollectResponse,
    AuthenticatedBrowserLaunchRequest,
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
from apps.api.services.sources import (
    authenticated_browser_collect,
    authenticated_browser_launch,
    authenticated_browser_status,
    source_capture_import_job,
    source_capture_patch,
    source_capture_save_tracker,
    source_captures,
    source_dedupe,
    source_import_csv,
    source_import_json,
    source_import_text,
    source_import_url,
    source_imports,
    source_stats,
)

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("/imports", response_model=ApiEnvelope[SourceImportsResponse])
def imports() -> ApiEnvelope[SourceImportsResponse]:
    """List imported opportunities and batches."""
    return ok(source_imports())


@router.post("/imports/text", response_model=ApiEnvelope[SourceImportResponse])
def import_text(payload: SourceImportTextRequest) -> ApiEnvelope[SourceImportResponse]:
    """Import pasted job text into the opportunity inbox."""
    data, warnings = source_import_text(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/imports/url", response_model=ApiEnvelope[SourceImportResponse])
def import_url(payload: SourceImportUrlRequest) -> ApiEnvelope[SourceImportResponse]:
    """Import one public URL or guide manual copy when blocked."""
    data, warnings = source_import_url(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/imports/csv", response_model=ApiEnvelope[SourceImportResponse])
def import_csv(payload: SourceImportCsvRequest) -> ApiEnvelope[SourceImportResponse]:
    """Import CSV rows into the opportunity inbox."""
    data, warnings = source_import_csv(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/imports/json", response_model=ApiEnvelope[SourceImportResponse])
def import_json(payload: SourceImportJsonRequest) -> ApiEnvelope[SourceImportResponse]:
    """Import JSON rows into the opportunity inbox."""
    data, warnings = source_import_json(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.get("/captures", response_model=ApiEnvelope[SourceCapturesResponse])
def captures() -> ApiEnvelope[SourceCapturesResponse]:
    """List persistent source captures."""
    return ok(source_captures())


@router.patch("/captures/{capture_id}", response_model=ApiEnvelope[SourceCaptureResponse])
def patch_capture(
    capture_id: str,
    payload: SourceCapturePatchRequest,
) -> ApiEnvelope[SourceCaptureResponse]:
    """Update one source capture."""
    return ok(source_capture_patch(capture_id, payload), request_id=payload.request_id)


@router.post(
    "/captures/{capture_id}/import-job",
    response_model=ApiEnvelope[SourceCaptureImportJobResponse],
)
def import_capture_job(capture_id: str) -> ApiEnvelope[SourceCaptureImportJobResponse]:
    """Import one source capture into the Vaga flow."""
    return ok(source_capture_import_job(capture_id))


@router.post(
    "/captures/{capture_id}/save-tracker",
    response_model=ApiEnvelope[SourceCaptureSaveTrackerResponse],
)
def save_capture_tracker(capture_id: str) -> ApiEnvelope[SourceCaptureSaveTrackerResponse]:
    """Save one source capture into the tracker."""
    return ok(source_capture_save_tracker(capture_id))


@router.post("/dedupe", response_model=ApiEnvelope[SourceDedupeResponse])
def dedupe() -> ApiEnvelope[SourceDedupeResponse]:
    """Run local duplicate detection for source inbox items."""
    return ok(source_dedupe())


@router.get("/stats", response_model=ApiEnvelope[SourceStatsResponse])
def stats() -> ApiEnvelope[SourceStatsResponse]:
    """Return source inbox stats."""
    return ok(source_stats())


@router.get(
    "/authenticated-browser/status",
    response_model=ApiEnvelope[AuthenticatedBrowserStatusResponse],
)
def browser_status(
    browser_cdp_url: str = DEFAULT_CDP_URL,
) -> ApiEnvelope[AuthenticatedBrowserStatusResponse]:
    """Inspect the local CDP browser session."""
    return ok(authenticated_browser_status(browser_cdp_url))


@router.post(
    "/authenticated-browser/launch",
    response_model=ApiEnvelope[AuthenticatedBrowserStatusResponse],
)
def browser_launch(
    payload: AuthenticatedBrowserLaunchRequest,
) -> ApiEnvelope[AuthenticatedBrowserStatusResponse]:
    """Open the dedicated browser so the user can log in manually."""
    return ok(authenticated_browser_launch(payload), request_id=payload.request_id)


@router.post(
    "/authenticated-browser/collect",
    response_model=ApiEnvelope[AuthenticatedBrowserCollectResponse],
)
def browser_collect(
    payload: AuthenticatedBrowserCollectRequest,
) -> ApiEnvelope[AuthenticatedBrowserCollectResponse]:
    """Collect opportunities from an authorized authenticated browser session."""
    return ok(authenticated_browser_collect(payload), request_id=payload.request_id)
