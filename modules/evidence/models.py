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


def reconcile_review_status(
    review_status: EvidenceReviewStatus,
    *,
    confirmed_by_user: bool,
    has_source: bool,
) -> tuple[EvidenceReviewStatus, bool]:
    """Return the consistent ``(review_status, confirmed_by_user)`` pair.

    Only the user confirms: ``confirmed_by_user`` and ``CONFIRMED`` imply each other; a source
    lifts a bare candidate to ``SOURCED`` (never to confirmed); rejected and stale items are never
    confirmed.
    """
    if confirmed_by_user:
        review_status = EvidenceReviewStatus.CONFIRMED
    elif review_status == EvidenceReviewStatus.CONFIRMED:
        confirmed_by_user = True
    elif review_status == EvidenceReviewStatus.CANDIDATE and has_source:
        review_status = EvidenceReviewStatus.SOURCED
    if review_status in {EvidenceReviewStatus.REJECTED, EvidenceReviewStatus.STALE}:
        confirmed_by_user = False
    return review_status, confirmed_by_user


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
