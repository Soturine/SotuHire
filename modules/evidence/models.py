"""Small dependency-free evidence primitives shared across domains."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceReviewStatus(StrEnum):
    """Human review state; provenance alone never means confirmation."""

    CANDIDATE = "candidate"
    SOURCED = "sourced"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    STALE = "stale"


class EvidenceSourceLocation(BaseModel):
    """Stable location inside an imported or captured source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str = ""
    document_kind: str = ""
    page_number: int | None = Field(default=None, ge=1)
    section_id: str = ""
    entry_id: str = ""
    block_id: str = ""
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
