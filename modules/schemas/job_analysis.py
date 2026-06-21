"""Structured output schema for job analysis."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Recommendation = Literal["apply", "apply_with_adjustments", "save_for_later", "ignore"]


class JobAnalysisSchema(BaseModel):
    """Validated output for CV x job analysis."""

    model_config = ConfigDict(extra="forbid")

    match_score: int = Field(ge=0, le=100)
    ats_score: int = Field(ge=0, le=100)
    opportunity_fit_score: int = Field(ge=0, le=100)
    risk_score: int = Field(ge=0, le=100)
    recommendation: Recommendation

    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    tailored_summary: str = ""
    recruiter_message: str = ""
    analysis_version: Literal["legacy", "match_engine_v2"] = "legacy"
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_score: int = Field(default=0, ge=0, le=100)
    matched_requirements: list[str] = Field(default_factory=list)
    partial_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    critical_gaps: list[str] = Field(default_factory=list)
    transferable_skills: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    safe_actions: list[str] = Field(default_factory=list)
    resume_improvements: list[str] = Field(default_factory=list)
    portfolio_github_improvements: list[str] = Field(default_factory=list)
    score_reasoning: list[str] = Field(default_factory=list)
    ats_present_keywords: list[str] = Field(default_factory=list)
    ats_missing_but_safe_to_add: list[str] = Field(default_factory=list)
    ats_missing_without_evidence: list[str] = Field(default_factory=list)

    def should_apply(self) -> bool:
        """Return True when the recommendation is positive enough to act."""
        return self.recommendation in {"apply", "apply_with_adjustments"}
