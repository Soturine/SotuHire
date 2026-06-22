"""Common API DTOs."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


class ApiError(BaseModel):
    """Stable error shape for frontend clients."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ApiEnvelope(BaseModel, Generic[DataT]):
    """Success envelope used by all v1 endpoints."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    data: DataT
    warnings: list[str] = Field(default_factory=list)
    request_id: str = ""


class ErrorEnvelope(BaseModel):
    """Error envelope used by exception handlers."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = False
    error: ApiError
    request_id: str = ""


class HealthResponse(BaseModel):
    """Health payload returned by the local frontend API."""

    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    service: str = "sotuhire-api"
    version: str
    local_first: bool = True
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    capabilities: list[str] = Field(default_factory=list)
    cors_allowed_origins: list[str] = Field(default_factory=list)
