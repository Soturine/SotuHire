"""Small structured outputs for optional AI insights around deterministic analyses."""

from __future__ import annotations

from pydantic import Field

from modules.ai.schemas.common import StrictSchema


class AtsAiReviewOutput(StrictSchema):
    """Evidence-only ATS observations produced by an optional provider."""

    keyword_observations: list[str] = Field(default_factory=list)
    safe_to_add_if_true: list[str] = Field(default_factory=list)
    missing_without_evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class ResumeTailorAiOutput(StrictSchema):
    """Evidence-backed tailoring ideas produced by an optional provider."""

    safe_keywords: list[str] = Field(default_factory=list)
    suggested_bullets: list[str] = Field(default_factory=list)
    conditional_suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class SafeAiInsightOutput(StrictSchema):
    """Generic safe observations for analyses whose final score remains code-owned."""

    insights: list[str] = Field(default_factory=list)
    safe_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
