"""Small structured outputs for optional AI insights around deterministic analyses."""

from __future__ import annotations

from typing import Literal

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


class SourceImportEnrichmentOutput(StrictSchema):
    """Optional evidence-only enrichment for imported opportunity intake."""

    tags: list[str] = Field(default_factory=list)
    domain: str = ""
    seniority: str = ""
    priority: str = ""
    summary: str = ""
    duplicate_explanation: str = ""
    inconsistency_alerts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class RadarMatchExplanationOutput(StrictSchema):
    """Optional evidence-only explanation for Job Radar matches."""

    summary: str = ""
    match_reasons: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    domain: str = ""
    seniority: str = ""
    warnings: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class WishlistDraftPayload(StrictSchema):
    """Structured but unsaved wishlist suggestion for Job Radar."""

    name: str = "Wishlist sugerida"
    target_titles: list[str] = Field(default_factory=list)
    target_domains: list[str] = Field(default_factory=list)
    target_seniority: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_preferences: list[str] = Field(default_factory=list)
    work_model: str = ""
    employment_type: str = ""
    salary_min: int | None = Field(default=None, ge=0)
    salary_currency: str = "BRL"
    contract_types: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    companies_include: list[str] = Field(default_factory=list)
    companies_exclude: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
    min_match_score: int = Field(default=70, ge=0, le=100)
    min_ats_score: int = Field(default=60, ge=0, le=100)
    notify_on_new_matches: bool = True
    is_active: bool = True
    notes: str = ""


class WishlistDraftOutput(StrictSchema):
    """Validated response for AI/local free-text wishlist drafting."""

    wishlist: WishlistDraftPayload = Field(default_factory=WishlistDraftPayload)
    confidence: float = Field(default=0.0, ge=0, le=1)
    detected_domains: list[str] = Field(default_factory=list)
    detected_career_moments: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    questions_to_confirm: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    needs_user_review: bool = True
    provider_used: str = "local"
    analysis_mode: Literal["ai", "local", "fallback"] = "local"
