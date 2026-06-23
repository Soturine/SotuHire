"""DTOs for local settings endpoints."""

from __future__ import annotations

from typing import Literal

from modules.ai.setup import DEFAULT_GEMINI_MODEL
from pydantic import BaseModel, ConfigDict, Field

AiProvider = Literal["local", "gemini", "openai_future"]
AiSettingsStatus = Literal["ready", "configured", "not_configured", "planned", "error"]


class AiSettingsResponse(BaseModel):
    """Safe AI settings payload returned to frontend clients."""

    model_config = ConfigDict(extra="forbid")

    provider: AiProvider = "local"
    model: str = "local"
    configured: bool = True
    status: AiSettingsStatus = "ready"
    use_ai: bool = False
    allow_match: bool = True
    allow_ats: bool = True
    allow_tailor: bool = True
    allow_github: bool = True
    allow_memory_context: bool = False
    updated_at: str = ""
    warnings: list[str] = Field(default_factory=list)


class AiSettingsUpdateRequest(BaseModel):
    """Update local AI provider settings without returning secrets."""

    model_config = ConfigDict(extra="forbid")

    provider: AiProvider = "local"
    model: str = Field(default=DEFAULT_GEMINI_MODEL, max_length=120)
    api_key: str | None = Field(default=None, max_length=5000)
    use_ai: bool = False
    allow_match: bool = True
    allow_ats: bool = True
    allow_tailor: bool = True
    allow_github: bool = True
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
