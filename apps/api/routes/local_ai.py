"""Explicit local AI interoperability and task-capability endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from modules.ai.local_interop import (
    DEFAULT_LOCAL_ENDPOINTS,
    LocalAiHealth,
    LocalAiProviderId,
    local_ai_health,
)
from modules.ai.provider_routing import AiTaskProviderRoute, provider_task_matrix
from pydantic import BaseModel, ConfigDict, Field

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope

router = APIRouter(prefix="/api/v1/ai/local", tags=["local-ai"])


class LocalAiCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: LocalAiProviderId
    endpoint: str = Field(default="", max_length=2048)
    advanced_remote_opt_in: bool = False
    api_key: str = Field(default="", max_length=5000)


@router.get("/defaults", response_model=ApiEnvelope[dict[str, str]])
def local_ai_defaults() -> ApiEnvelope[dict[str, str]]:
    """List documented loopback defaults without probing any endpoint."""
    return ok({str(provider): endpoint for provider, endpoint in DEFAULT_LOCAL_ENDPOINTS.items()})


@router.post("/health", response_model=ApiEnvelope[LocalAiHealth])
def check_local_ai(payload: LocalAiCheckRequest) -> ApiEnvelope[LocalAiHealth]:
    """Check only the endpoint explicitly submitted by the user."""
    return ok(
        local_ai_health(
            payload.provider,
            payload.endpoint,
            advanced_remote_opt_in=payload.advanced_remote_opt_in,
            api_key=payload.api_key,
        )
    )


@router.get("/routing", response_model=ApiEnvelope[list[AiTaskProviderRoute]])
def local_ai_routing() -> ApiEnvelope[list[AiTaskProviderRoute]]:
    """Return the complete task/prompt/schema/context/provider wiring matrix."""
    return ok(provider_task_matrix())


__all__ = ["router"]
