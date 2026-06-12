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

    def should_apply(self) -> bool:
        """Return True when the recommendation is positive enough to act."""
        return self.recommendation in {"apply", "apply_with_adjustments"}
