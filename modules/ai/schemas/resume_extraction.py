"""Structured AI schema for resume extraction."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from modules.ai.schemas.common import (
    ConfidenceSummary,
    CredentialSignal,
    DomainSignal,
    LanguageSignal,
    StrictSchema,
)


class CandidateIdentity(StrictSchema):
    """Candidate identity and contact presence extracted from a resume."""

    name: str = ""
    email: str = ""
    email_present: bool = False
    phone: str = ""
    phone_present: bool = False
    location: str = ""
    links: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ProfessionalSummary(StrictSchema):
    """Headline and summary evidence from the resume."""

    current_headline: str = ""
    inferred_headline: str = ""
    summary_text: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SenioritySignal(StrictSchema):
    """Estimated seniority with conservative confidence."""

    estimated_level: Literal[
        "intern",
        "apprentice",
        "assistant",
        "junior",
        "mid",
        "senior",
        "specialist",
        "coordinator",
        "manager",
        "unknown",
    ] = "unknown"
    reasoning: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class EducationEntry(StrictSchema):
    """Education item without converting courses into certifications."""

    course: str = ""
    institution: str = ""
    degree_type: Literal[
        "technical",
        "bachelor",
        "licentiate",
        "postgraduate",
        "mba",
        "course",
        "certification",
        "high_school",
        "unknown",
    ] = "unknown"
    status: Literal["completed", "ongoing", "interrupted", "unknown"] = "unknown"
    start_date: str = ""
    end_date: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExperienceEntry(StrictSchema):
    """Professional experience item, separated from projects."""

    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    tools_or_methods: list[str] = Field(default_factory=list)
    domain: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ProjectEntry(StrictSchema):
    """Project evidence that must not be promoted to corporate experience."""

    name: str = ""
    description: str = ""
    technologies_or_methods: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractedSkill(StrictSchema):
    """Skill, tool, software, equipment or domain knowledge from a resume."""

    name: str
    normalized_name: str = ""
    category: Literal[
        "hard_skill",
        "soft_skill",
        "tool",
        "software",
        "equipment",
        "methodology",
        "language",
        "certification",
        "professional_license",
        "regulation",
        "domain_knowledge",
        "other",
    ] = "other"
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AtsObservations(StrictSchema):
    """Resume structure and ATS risks detected during extraction."""

    missing_sections: list[str] = Field(default_factory=list)
    weak_sections: list[str] = Field(default_factory=list)
    strong_sections: list[str] = Field(default_factory=list)
    format_risks: list[str] = Field(default_factory=list)
    keyword_risks: list[str] = Field(default_factory=list)


class ResumeExtractionOutput(StrictSchema):
    """Structured, confidence-aware resume extraction result."""

    candidate_identity: CandidateIdentity = Field(default_factory=CandidateIdentity)
    professional_summary: ProfessionalSummary = Field(default_factory=ProfessionalSummary)
    domains: list[DomainSignal] = Field(default_factory=list)
    seniority: SenioritySignal = Field(default_factory=SenioritySignal)
    education: list[EducationEntry] = Field(default_factory=list)
    experiences: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    skills: list[ExtractedSkill] = Field(default_factory=list)
    tools: list[ExtractedSkill] = Field(default_factory=list)
    softwares: list[ExtractedSkill] = Field(default_factory=list)
    equipment: list[ExtractedSkill] = Field(default_factory=list)
    certifications: list[CredentialSignal] = Field(default_factory=list)
    professional_licenses: list[CredentialSignal] = Field(default_factory=list)
    languages: list[LanguageSignal] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    ats_observations: AtsObservations = Field(default_factory=AtsObservations)
    extraction_confidence: ConfidenceSummary = Field(default_factory=ConfidenceSummary)
