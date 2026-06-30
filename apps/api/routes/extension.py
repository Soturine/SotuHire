"""Frontend bridge routes for the existing browser extension companion."""

from __future__ import annotations

from fastapi import APIRouter, Query

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.extension import (
    ExtensionAddToProfileResponse,
    ExtensionCapturePatchRequest,
    ExtensionCapturePatchResponse,
    ExtensionCapturesResponse,
    ExtensionContextResponse,
    ExtensionImportGithubResponse,
    ExtensionImportJobResponse,
    ExtensionImportRequest,
    ExtensionImportTrackerResponse,
    ExtensionProfileCandidatesRequest,
    ExtensionProfileCandidatesResponse,
    ExtensionStatusResponse,
)
from apps.api.services.extension import (
    extension_capture_add_to_profile,
    extension_capture_profile_candidates,
    extension_captures,
    extension_context,
    extension_import_github,
    extension_import_job,
    extension_import_tracker,
    extension_patch_capture,
    extension_project_add_to_profile,
    extension_project_profile_candidates,
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


@router.get("/context", response_model=ApiEnvelope[ExtensionContextResponse])
def local_extension_context() -> ApiEnvelope[ExtensionContextResponse]:
    """Return unified local context for extension/profile review."""
    return ok(extension_context())


@router.patch(
    "/captures/{capture_id}",
    response_model=ApiEnvelope[ExtensionCapturePatchResponse],
)
def local_extension_patch_capture(
    capture_id: str,
    payload: ExtensionCapturePatchRequest,
) -> ApiEnvelope[ExtensionCapturePatchResponse]:
    """Archive, ignore, or mark a local extension capture as reviewed."""
    return ok(extension_patch_capture(capture_id, payload), request_id=payload.request_id)


@router.post(
    "/captures/{capture_id}/profile-candidates",
    response_model=ApiEnvelope[ExtensionProfileCandidatesResponse],
)
def local_extension_capture_profile_candidates(
    capture_id: str,
) -> ApiEnvelope[ExtensionProfileCandidatesResponse]:
    """Generate review-only profile candidates from a capture."""
    return ok(extension_capture_profile_candidates(capture_id))


@router.post(
    "/captures/{capture_id}/add-to-profile",
    response_model=ApiEnvelope[ExtensionAddToProfileResponse],
)
def local_extension_capture_add_to_profile(
    capture_id: str,
    payload: ExtensionProfileCandidatesRequest,
) -> ApiEnvelope[ExtensionAddToProfileResponse]:
    """Add selected capture candidates to the profile after user review."""
    return ok(extension_capture_add_to_profile(capture_id, payload), request_id=payload.request_id)


@router.post(
    "/projects/{project_id}/profile-candidates",
    response_model=ApiEnvelope[ExtensionProfileCandidatesResponse],
)
def local_extension_project_profile_candidates(
    project_id: str,
) -> ApiEnvelope[ExtensionProfileCandidatesResponse]:
    """Generate review-only profile candidates from a saved project."""
    return ok(extension_project_profile_candidates(project_id))


@router.post(
    "/projects/{project_id}/add-to-profile",
    response_model=ApiEnvelope[ExtensionAddToProfileResponse],
)
def local_extension_project_add_to_profile(
    project_id: str,
    payload: ExtensionProfileCandidatesRequest,
) -> ApiEnvelope[ExtensionAddToProfileResponse]:
    """Add selected project candidates to the profile after user review."""
    return ok(extension_project_add_to_profile(project_id, payload), request_id=payload.request_id)


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
