"""Structured AI schema for multi-domain job extraction."""

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

RequirementCategory = Literal[
    "education",
    "hard_skill",
    "soft_skill",
    "tool",
    "software",
    "equipment",
    "certification",
    "professional_license",
    "language",
    "experience",
    "methodology",
    "regulation",
    "responsibility",
    "availability",
    "location",
    "portfolio",
    "other",
]
RequirementImportance = Literal["required", "preferred", "optional", "unclear"]
RequirementCriticality = Literal["low", "medium", "high", "knockout"]


class SalaryInfo(StrictSchema):
    """Salary range or raw salary text from a job posting."""

    raw: str = ""
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    currency: str = "BRL"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class JobIdentity(StrictSchema):
    """Identity and logistics for a job posting."""

    title: str = ""
    company: str = ""
    source: str = ""
    url: str = ""
    location: str = ""
    work_model: Literal["remote", "hybrid", "onsite", "field", "unknown"] = "unknown"
    contract_type: Literal[
        "clt",
        "pj",
        "internship",
        "temporary",
        "freelance",
        "trainee",
        "apprentice",
        "public_sector",
        "unknown",
    ] = "unknown"
    salary: SalaryInfo = Field(default_factory=SalaryInfo)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class JobDomainClassification(StrictSchema):
    """Domain classification embedded in a job extraction."""

    primary_domain: str = "unknown"
    secondary_domains: list[str] = Field(default_factory=list)
    is_tech_job: bool = False
    is_regulated_profession: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class JobSeniority(StrictSchema):
    """Job seniority requirement."""

    level: Literal[
        "intern",
        "apprentice",
        "assistant",
        "junior",
        "mid",
        "senior",
        "specialist",
        "coordinator",
        "manager",
        "director",
        "unknown",
    ] = "unknown"
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class JobRequirement(StrictSchema):
    """Normalized requirement extracted from a job posting."""

    text: str
    normalized_name: str = ""
    category: RequirementCategory = "other"
    importance: RequirementImportance = "unclear"
    criticality: RequirementCriticality = "medium"
    domain: str = ""
    evidence: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RedFlag(StrictSchema):
    """Risk or ambiguity in the job posting."""

    type: Literal[
        "vague_salary",
        "excessive_requirements",
        "unpaid_work",
        "suspicious_contact",
        "unrealistic_seniority",
        "discrimination",
        "missing_information",
        "other",
    ] = "other"
    description: str = ""
    severity: Literal["low", "medium", "high"] = "low"


class JobExtractionOutput(StrictSchema):
    """Structured, multi-domain job extraction result."""

    job_identity: JobIdentity = Field(default_factory=JobIdentity)
    domain_classification: JobDomainClassification = Field(default_factory=JobDomainClassification)
    domains: list[DomainSignal] = Field(default_factory=list)
    seniority: JobSeniority = Field(default_factory=JobSeniority)
    requirements: list[JobRequirement] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    tools: list[JobRequirement] = Field(default_factory=list)
    softwares: list[JobRequirement] = Field(default_factory=list)
    equipment: list[JobRequirement] = Field(default_factory=list)
    certifications: list[CredentialSignal] = Field(default_factory=list)
    professional_licenses: list[CredentialSignal] = Field(default_factory=list)
    education_requirements: list[JobRequirement] = Field(default_factory=list)
    languages: list[LanguageSignal] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)
    keywords_for_ats: list[str] = Field(default_factory=list)
    missing_job_information: list[str] = Field(default_factory=list)
    extraction_confidence: ConfidenceSummary = Field(default_factory=ConfidenceSummary)
