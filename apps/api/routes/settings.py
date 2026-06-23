"""Local settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.settings import (
    AiSettingsResponse,
    AiSettingsTestRequest,
    AiSettingsTestResponse,
    AiSettingsUpdateRequest,
)
from apps.api.services.ai_settings import (
    delete_ai_settings_secret,
    get_ai_settings,
    get_ai_settings_status,
    save_ai_settings,
    test_ai_settings,
)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("/ai", response_model=ApiEnvelope[AiSettingsResponse])
def ai_settings() -> ApiEnvelope[AiSettingsResponse]:
    """Return safe local AI provider settings."""
    data = get_ai_settings()
    return ok(data, warnings=data.warnings)


@router.get("/ai/status", response_model=ApiEnvelope[AiSettingsResponse])
def ai_settings_status() -> ApiEnvelope[AiSettingsResponse]:
    """Return safe local AI provider status."""
    data = get_ai_settings_status()
    return ok(data, warnings=data.warnings)


@router.post("/ai", response_model=ApiEnvelope[AiSettingsResponse])
def ai_settings_save(payload: AiSettingsUpdateRequest) -> ApiEnvelope[AiSettingsResponse]:
    """Persist local AI provider settings without returning the key."""
    data = save_ai_settings(payload)
    return ok(data, warnings=data.warnings, request_id=payload.request_id)


@router.post("/ai/test", response_model=ApiEnvelope[AiSettingsTestResponse])
def ai_settings_test(payload: AiSettingsTestRequest) -> ApiEnvelope[AiSettingsTestResponse]:
    """Test local provider configuration safely."""
    return ok(test_ai_settings(payload), request_id=payload.request_id)


@router.delete("/ai", response_model=ApiEnvelope[AiSettingsResponse])
def ai_settings_delete() -> ApiEnvelope[AiSettingsResponse]:
    """Delete the backend-stored AI provider key."""
    data = delete_ai_settings_secret()
    return ok(data, warnings=data.warnings)
