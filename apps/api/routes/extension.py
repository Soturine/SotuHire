"""Frontend bridge routes for the existing browser extension companion."""

from __future__ import annotations

from fastapi import APIRouter, Query

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.extension import (
    ExtensionCapturesResponse,
    ExtensionImportGithubResponse,
    ExtensionImportJobResponse,
    ExtensionImportRequest,
    ExtensionImportTrackerResponse,
    ExtensionStatusResponse,
)
from apps.api.services.extension import (
    extension_captures,
    extension_import_github,
    extension_import_job,
    extension_import_tracker,
    extension_status,
)

router = APIRouter(prefix="/api/v1/extension", tags=["extension"])


@router.get("/status", response_model=ApiEnvelope[ExtensionStatusResponse])
def local_extension_status() -> ApiEnvelope[ExtensionStatusResponse]:
    """Return Local Companion bridge status for the web frontend."""
    return ok(extension_status())


@router.get("/captures", response_model=ApiEnvelope[ExtensionCapturesResponse])
def local_extension_captures(
    limit: int = Query(default=20, ge=1, le=100),
) -> ApiEnvelope[ExtensionCapturesResponse]:
    """Return recent captures created by the existing browser extension."""
    return ok(extension_captures(limit))


@router.get("/profile-analysis", response_model=ApiEnvelope[ExtensionStatusResponse])
def local_extension_profile_analysis() -> ApiEnvelope[ExtensionStatusResponse]:
    """Expose a safe placeholder for future profile analysis integration."""
    data = extension_status().model_copy(
        update={"message": "Analise de perfil pela extensao permanece no roadmap seguro."}
    )
    return ok(data)


@router.post("/import/job", response_model=ApiEnvelope[ExtensionImportJobResponse])
def local_extension_import_job(
    payload: ExtensionImportRequest,
) -> ApiEnvelope[ExtensionImportJobResponse]:
    """Import one local extension capture into the job extraction flow."""
    return ok(extension_import_job(payload), request_id=payload.request_id)


@router.post("/import/github", response_model=ApiEnvelope[ExtensionImportGithubResponse])
def local_extension_import_github(
    payload: ExtensionImportRequest,
) -> ApiEnvelope[ExtensionImportGithubResponse]:
    """Analyze one GitHub capture using existing local companion logic."""
    return ok(extension_import_github(payload), request_id=payload.request_id)


@router.post("/import/tracker", response_model=ApiEnvelope[ExtensionImportTrackerResponse])
def local_extension_import_tracker(
    payload: ExtensionImportRequest,
) -> ApiEnvelope[ExtensionImportTrackerResponse]:
    """Send one captured job to the local tracker."""
    return ok(extension_import_tracker(payload), request_id=payload.request_id)
