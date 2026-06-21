"""Typed contracts for Match Engine 2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MatchModel(BaseModel):
    """Base model for Match Engine 2 contracts."""

    model_config = ConfigDict(extra="forbid")


RequirementCategory = Literal[
    "education",
    "hard_skill",
    "soft_skill",
    "tool",
    "software",
    "equipment",
    "certification",
    "professional_license",
    "professional_registration",
    "language",
    "experience",
    "methodology",
    "regulation",
    "responsibility",
    "availability",
    "location",
    "portfolio",
    "domain_knowledge",
    "other",
]
RequirementImportance = Literal["required", "preferred", "optional", "unclear"]
RequirementCriticality = Literal["low", "medium", "high", "knockout"]
MatchStatus = Literal["matched", "partial", "missing", "unclear", "not_applicable"]
GapSeverity = Literal["none", "low", "medium", "high", "knockout"]
EvidenceSource = Literal["resume", "github", "portfolio", "memory", "profile", "manual", "none"]
EvidenceStrength = Literal["weak", "medium", "strong", "verified", "unclear"]
RecommendationAction = Literal["apply", "apply_with_adjustments", "save_for_later", "ignore"]

OTHER_PROFESSIONAL_REGISTRATION_OPTION = "Outro conselho / Outro registro profissional"


class ProfessionalRegistrationInput(MatchModel):
    """Optional user-provided professional registration form value."""

    type: Literal["professional_license", "professional_registration"] = "professional_license"
    council: str = ""
    region: str = ""
    number_present: bool = False
    status: Literal["active", "expired", "unknown", "not_informed"] = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class MatchRequirement(MatchModel):
    """A job requirement normalized for evidence-based matching."""

    requirement_text: str
    normalized_name: str = ""
    category: RequirementCategory = "other"
    importance: RequirementImportance = "unclear"
    criticality: RequirementCriticality = "medium"
    domain: str = ""
    evidence: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class CandidateEvidence(MatchModel):
    """Evidence available from resume, GitHub, portfolio, memory or profile."""

    skill: str
    normalized_name: str = ""
    category: RequirementCategory = "other"
    evidence_source: EvidenceSource = "none"
    evidence_text: str = ""
    evidence_file: str = ""
    strength: EvidenceStrength = "unclear"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RequirementMatch(MatchModel):
    """Result of comparing one requirement against candidate evidence."""

    requirement: MatchRequirement
    match_status: MatchStatus = "unclear"
    candidate_evidence: list[CandidateEvidence] = Field(default_factory=list)
    evidence_source: EvidenceSource = "none"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    gap_severity: GapSeverity = "medium"
    safe_action: str = ""


class CriticalGap(MatchModel):
    """Critical or high-severity gap with a safe action."""

    requirement: MatchRequirement
    severity: GapSeverity
    reason: str
    safe_action: str


class TransferableSkillMatch(MatchModel):
    """Transferable skill that can support, but not replace, a direct requirement."""

    original_skill: str
    target_requirement: str
    transfer_level: Literal["low", "medium", "high"]
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limitation: str = ""


class MatchScoreBreakdown(MatchModel):
    """Code-calculated score breakdown for Match Engine 2."""

    required_requirements_score: int = Field(ge=0, le=100)
    preferred_requirements_score: int = Field(ge=0, le=100)
    domain_fit_score: int = Field(ge=0, le=100)
    seniority_fit_score: int = Field(ge=0, le=100)
    education_credentials_score: int = Field(ge=0, le=100)
    evidence_strength_score: int = Field(ge=0, le=100)
    portfolio_github_evidence_score: int = Field(ge=0, le=100)
    ats_keyword_alignment_score: int = Field(ge=0, le=100)
    preferences_fit_score: int = Field(ge=0, le=100)
    risk_penalty: int = Field(ge=0, le=100)
    match_score: int = Field(ge=0, le=100)
    ats_alignment_score: int = Field(ge=0, le=100)
    opportunity_fit_score: int = Field(ge=0, le=100)
    evidence_score: int = Field(ge=0, le=100)
    risk_score: int = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0.0, le=1.0)
    overall_score: int = Field(ge=0, le=100)


class MatchExplanation(MatchModel):
    """Human-facing explanation for the match result."""

    summary: str = ""
    score_reasoning: list[str] = Field(default_factory=list)
    matched_requirements: list[str] = Field(default_factory=list)
    partial_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    critical_gaps: list[str] = Field(default_factory=list)
    transferable_skills: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    safe_actions: list[str] = Field(default_factory=list)
    resume_improvements: list[str] = Field(default_factory=list)
    portfolio_github_improvements: list[str] = Field(default_factory=list)


class MatchResultV2(MatchModel):
    """Final Match Engine 2 output."""

    requirements: list[MatchRequirement] = Field(default_factory=list)
    requirement_matches: list[RequirementMatch] = Field(default_factory=list)
    critical_gaps: list[CriticalGap] = Field(default_factory=list)
    transferable_skills: list[TransferableSkillMatch] = Field(default_factory=list)
    score_breakdown: MatchScoreBreakdown
    explanation: MatchExplanation
    recommendation: RecommendationAction
    fallback_used: bool = False
    provider_used: str = "local"
