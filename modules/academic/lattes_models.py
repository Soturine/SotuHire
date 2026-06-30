"""Models for pasted Lattes and academic evidence imports."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from modules.profile.models import ProfileConfidence, ProfileItem

AnalysisMode = Literal["local", "ai", "fallback"]


class LattesImportInput(BaseModel):
    """Input accepted by the local Lattes import flow."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=300_000)
    source_url: str = Field(default="", max_length=2048)
    lattes_id: str = Field(default="", max_length=160)
    orcid: str = Field(default="", max_length=80)
    use_ai: bool = False
    language: str = Field(default="pt-BR", max_length=20)


class LattesImportResult(BaseModel):
    """Review-only ProfileItem drafts extracted from Lattes-like text."""

    model_config = ConfigDict(extra="forbid")

    items: list[ProfileItem] = Field(default_factory=list)
    detected_sections: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    questions_to_confirm: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: ProfileConfidence = "medium"
    needs_user_review: bool = True
    provider_used: str = "local"
    requested_provider: str = "local"
    analysis_mode: AnalysisMode = "local"


class LattesConfirmResult(BaseModel):
    """Result of explicitly confirming selected academic profile items."""

    model_config = ConfigDict(extra="forbid")

    saved: list[ProfileItem] = Field(default_factory=list)
    skipped_duplicates: list[ProfileItem] = Field(default_factory=list)
    message: str = ""
