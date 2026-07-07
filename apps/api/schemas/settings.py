"""DTOs for local settings endpoints."""

from __future__ import annotations

from typing import Literal

from modules.ai.providers.openai_provider import DEFAULT_OPENAI_MODEL
from modules.ai.setup import DEFAULT_GEMINI_MODEL
from pydantic import BaseModel, ConfigDict, Field

AiProvider = Literal["local", "gemini", "openai", "openai_future"]
AiSettingsStatus = Literal["ready", "configured", "not_configured", "planned", "error"]
AiSettingsPreset = Literal["local_safe", "basic", "complete", "custom"]
AiModelSource = Literal["cache", "provider_api", "builtin"]


class AiSettingsResponse(BaseModel):
    """Safe AI settings payload returned to frontend clients."""

    model_config = ConfigDict(extra="forbid")

    provider: AiProvider = "local"
    model: str = "local"
    configured: bool = True
    status: AiSettingsStatus = "ready"
    preset: AiSettingsPreset = "local_safe"
    use_ai: bool = False
    allow_profile: bool = True
    allow_lattes: bool = True
    allow_resume: bool = True
    allow_job: bool = True
    allow_public_exams: bool = True
    allow_match: bool = True
    allow_ats: bool = True
    allow_tailor: bool = True
    allow_github: bool = True
    allow_source_import: bool = True
    allow_extension: bool = True
    allow_radar: bool = True
    allow_notifications: bool = True
    allow_memory_context: bool = False
    updated_at: str = ""
    warnings: list[str] = Field(default_factory=list)


class AiSettingsUpdateRequest(BaseModel):
    """Update local AI provider settings without returning secrets."""

    model_config = ConfigDict(extra="forbid")

    provider: AiProvider = "local"
    model: str = Field(default=DEFAULT_GEMINI_MODEL, max_length=120)
    api_key: str | None = Field(default=None, max_length=5000)
    preset: AiSettingsPreset = "custom"
    use_ai: bool = False
    allow_profile: bool = True
    allow_lattes: bool = True
    allow_resume: bool = True
    allow_job: bool = True
    allow_public_exams: bool = True
    allow_match: bool = True
    allow_ats: bool = True
    allow_tailor: bool = True
    allow_github: bool = True
    allow_source_import: bool = True
    allow_extension: bool = True
    allow_radar: bool = True
    allow_notifications: bool = True
    allow_memory_context: bool = False
    request_id: str = Field(default="", max_length=120)


class AiSettingsTestRequest(BaseModel):
    """Test a configured or just-submitted provider."""

    model_config = ConfigDict(extra="forbid")

    provider: AiProvider | None = None
    model: str | None = Field(default=None, max_length=120)
    api_key: str | None = Field(default=None, max_length=5000)
    request_id: str = Field(default="", max_length=120)


class AiSettingsTestResponse(BaseModel):
    """Safe result of a user-triggered provider test."""

    model_config = ConfigDict(extra="forbid")

    provider: AiProvider
    model: str
    success: bool
    configured: bool
    status: AiSettingsStatus
    message: str


class AiProviderInfo(BaseModel):
    """Safe provider info for settings UI."""

    model_config = ConfigDict(extra="forbid")

    id: Literal["local", "gemini", "openai"]
    label: str
    status: str = "available"
    requires_api_key: bool = False
    key_url: str = ""
    supports_model_catalog: bool = False
    warnings: list[str] = Field(default_factory=list)


class AiProvidersResponse(BaseModel):
    """List of configured/available AI providers."""

    model_config = ConfigDict(extra="forbid")

    providers: list[AiProviderInfo] = Field(default_factory=list)


class AiModelInfo(BaseModel):
    """Safe model entry exposed to frontend clients."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    status: str = "known"
    supports_structured_output: bool = True
    supports_json: bool = True
    recommended_for: list[str] = Field(default_factory=list)


class AiModelsResponse(BaseModel):
    """Provider model catalog response."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["local", "gemini", "openai"]
    models: list[AiModelInfo] = Field(default_factory=list)
    source: AiModelSource = "builtin"
    updated_at: str = ""
    warnings: list[str] = Field(default_factory=list)


class AiModelsRefreshRequest(BaseModel):
    """User-triggered provider model refresh."""

    model_config = ConfigDict(extra="forbid")

    provider: Literal["gemini", "openai"]
    request_id: str = Field(default="", max_length=120)


def default_model_for_provider(provider: AiProvider) -> str:
    """Small schema helper reused by OpenAPI docs/tests."""
    if provider == "local":
        return "local"
    if provider == "openai":
        return DEFAULT_OPENAI_MODEL
    return DEFAULT_GEMINI_MODEL
