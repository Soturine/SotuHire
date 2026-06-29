"""Universal Career Profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.profile import (
    ProfileContextResponse,
    ProfileDeduplicateResponse,
    ProfileImportTextRequest,
    ProfileImportTextResponse,
    ProfileItemPatchRequest,
    ProfileItemRequest,
    ProfileItemResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from apps.api.services.profile import (
    profile_add_item,
    profile_context,
    profile_deduplicate,
    profile_delete_item,
    profile_get,
    profile_import_text,
    profile_patch_item,
    profile_update,
)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("", response_model=ApiEnvelope[ProfileResponse])
def get_profile() -> ApiEnvelope[ProfileResponse]:
    """Return the active local universal profile."""
    return ok(profile_get())


@router.put("", response_model=ApiEnvelope[ProfileResponse])
def put_profile(payload: ProfileUpdateRequest) -> ApiEnvelope[ProfileResponse]:
    """Update the active profile metadata."""
    return ok(profile_update(payload), request_id=payload.request_id)


@router.post("/items", response_model=ApiEnvelope[ProfileItemResponse])
def add_profile_item(payload: ProfileItemRequest) -> ApiEnvelope[ProfileItemResponse]:
    """Add one reviewed item to the profile."""
    return ok(profile_add_item(payload), request_id=payload.request_id)


@router.patch("/items/{item_id}", response_model=ApiEnvelope[ProfileItemResponse])
def patch_profile_item(
    item_id: str,
    payload: ProfileItemPatchRequest,
) -> ApiEnvelope[ProfileItemResponse]:
    """Patch one profile item."""
    return ok(profile_patch_item(item_id, payload), request_id=payload.request_id)


@router.delete("/items/{item_id}", response_model=ApiEnvelope[ProfileResponse])
def delete_profile_item(item_id: str) -> ApiEnvelope[ProfileResponse]:
    """Delete one profile item."""
    return ok(profile_delete_item(item_id))


@router.post("/import-text", response_model=ApiEnvelope[ProfileImportTextResponse])
def import_profile_text(
    payload: ProfileImportTextRequest,
) -> ApiEnvelope[ProfileImportTextResponse]:
    """Extract draft profile items from pasted text."""
    data, warnings = profile_import_text(payload)
    return ok(data, warnings=warnings, request_id=payload.request_id)


@router.post("/deduplicate", response_model=ApiEnvelope[ProfileDeduplicateResponse])
def deduplicate_profile() -> ApiEnvelope[ProfileDeduplicateResponse]:
    """Return safe profile duplicate suggestions."""
    return ok(profile_deduplicate())


@router.get("/context", response_model=ApiEnvelope[ProfileContextResponse])
def get_profile_context() -> ApiEnvelope[ProfileContextResponse]:
    """Return compact local profile context for downstream workflows."""
    return ok(profile_context())
