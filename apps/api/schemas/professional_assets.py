"""HTTP contracts for local professional assets."""

from __future__ import annotations

from typing import Literal

from modules.professional_assets import ProfessionalAsset
from pydantic import BaseModel, ConfigDict, Field


class AssetApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfessionalAssetCreateRequest(AssetApiModel):
    asset: ProfessionalAsset
    request_id: str = Field(default="", max_length=120)


class ProfessionalAssetUpdateRequest(AssetApiModel):
    content: str | None = Field(default=None, max_length=100_000)
    title: str | None = Field(default=None, max_length=240)
    request_id: str = Field(default="", max_length=120)


class ProfessionalAssetStatusRequest(AssetApiModel):
    status: Literal["draft", "review", "confirmed", "archived", "stale"]
    content: str | None = Field(default=None, max_length=100_000)
    request_id: str = Field(default="", max_length=120)


class ProfessionalAssetResponse(AssetApiModel):
    asset: ProfessionalAsset


class ProfessionalAssetPage(AssetApiModel):
    items: list[ProfessionalAsset]
    limit: int
    offset: int


__all__ = [
    "ProfessionalAssetCreateRequest",
    "ProfessionalAssetPage",
    "ProfessionalAssetResponse",
    "ProfessionalAssetStatusRequest",
    "ProfessionalAssetUpdateRequest",
]
