"""Structured report schemas for GitHub Analyzer 2."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from modules.github_analyzer.evidence_index import EvidenceItem
from modules.github_analyzer.repository_models import RepositoryAnalyzerModel

Grade = Literal["A", "B", "C", "D", "F"]
RiskLevel = Literal["low", "medium", "high", "critical", "unclear"]


class DimensionScores(RepositoryAnalyzerModel):
    """AI/intermediate dimension scores on a 0..10 scale."""

    tests: int = Field(default=0, ge=0, le=10)
    security: int = Field(default=0, ge=0, le=10)
    architecture: int = Field(default=0, ge=0, le=10)
    code_quality: int = Field(default=0, ge=0, le=10)
    documentation: int = Field(default=0, ge=0, le=10)
    consistency: int = Field(default=0, ge=0, le=10)
    maintainability: int = Field(default=0, ge=0, le=10)
    portfolio_value: int = Field(default=0, ge=0, le=10)
    resume_evidence: int = Field(default=0, ge=0, le=10)
    recruiter_readiness: int = Field(default=0, ge=0, le=10)
    job_alignment: int = Field(default=0, ge=0, le=10)


class RepositoryIdentityAssessment(RepositoryAnalyzerModel):
    """Repository identity as interpreted by analysis."""

    owner: str = ""
    name: str = ""
    url: str = ""
    project_type: str = "unknown"
    detected_domains: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class ExecutiveSummary(RepositoryAnalyzerModel):
    """Short summaries for different reading contexts."""

    short_summary: str = ""
    professional_summary: str = ""
    recruiter_summary: str = ""
    limitations: list[str] = Field(default_factory=list)


class TechnologyEvidence(RepositoryAnalyzerModel):
    """Technology detected from a concrete file."""

    technology: str
    evidence_file: str
    confidence: float = Field(ge=0, le=1)


class TechStackAssessment(RepositoryAnalyzerModel):
    """Detected stack grouped by category."""

    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    libraries: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    devops: list[str] = Field(default_factory=list)
    testing_tools: list[str] = Field(default_factory=list)
    detected_from_files: list[TechnologyEvidence] = Field(default_factory=list)


class ImportantModule(RepositoryAnalyzerModel):
    """Important module with evidence path."""

    path: str
    role: str = ""
    evidence: str = ""


class ArchitectureAssessment(RepositoryAnalyzerModel):
    """Repository architecture interpretation."""

    rating: Literal["excellent", "good", "fair", "poor", "unclear"] = "unclear"
    style: str = "unknown"
    entry_points: list[str] = Field(default_factory=list)
    important_modules: list[ImportantModule] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)


class SkillEvidence(RepositoryAnalyzerModel):
    """Skill supported by repository files."""

    skill: str
    category: str = "technical"
    evidence_files: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class PortfolioValueAssessment(RepositoryAnalyzerModel):
    """Career-facing value of a repository."""

    best_fit_roles: list[str] = Field(default_factory=list)
    skills_demonstrated: list[SkillEvidence] = Field(default_factory=list)
    career_strengths: list[str] = Field(default_factory=list)
    career_weaknesses: list[str] = Field(default_factory=list)
    how_to_present_in_interview: list[str] = Field(default_factory=list)


class SafeResumeBullet(RepositoryAnalyzerModel):
    """Resume bullet that is backed by repository evidence."""

    bullet: str
    supported_by: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    risk_of_overclaiming: Literal["low", "medium", "high"] = "medium"


class ResumeEvidenceAssessment(RepositoryAnalyzerModel):
    """Resume-ready evidence and guardrails."""

    safe_resume_bullets: list[SafeResumeBullet] = Field(default_factory=list)
    skills_to_add_if_true: list[str] = Field(default_factory=list)
    do_not_claim: list[str] = Field(default_factory=list)


class SecurityFlag(RepositoryAnalyzerModel):
    """Security issue or risk indicator."""

    severity: Literal["low", "medium", "high", "critical"]
    type: str
    description: str
    evidence_file: str = ""
    recommendation: str = ""


class SecurityAssessment(RepositoryAnalyzerModel):
    """Security interpretation for sampled repository evidence."""

    risk_level: RiskLevel = "unclear"
    security_flags: list[SecurityFlag] = Field(default_factory=list)
    positive_security_signals: list[str] = Field(default_factory=list)


class FinalVerdict(RepositoryAnalyzerModel):
    """Final portfolio readiness verdict."""

    is_portfolio_ready: bool = False
    main_blockers: list[str] = Field(default_factory=list)
    next_3_actions: list[str] = Field(default_factory=list)
    one_sentence_verdict: str = ""


class GitHubRepoAnalysisOutput(RepositoryAnalyzerModel):
    """Structured provider output for github_repo_analysis_v2."""

    repository_identity: RepositoryIdentityAssessment = Field(
        default_factory=RepositoryIdentityAssessment
    )
    executive_summary: ExecutiveSummary = Field(default_factory=ExecutiveSummary)
    dimension_scores: DimensionScores = Field(default_factory=DimensionScores)
    tech_stack: TechStackAssessment = Field(default_factory=TechStackAssessment)
    architecture: ArchitectureAssessment = Field(default_factory=ArchitectureAssessment)
    portfolio_value: PortfolioValueAssessment = Field(default_factory=PortfolioValueAssessment)
    resume_evidence: ResumeEvidenceAssessment = Field(default_factory=ResumeEvidenceAssessment)
    security: SecurityAssessment = Field(default_factory=SecurityAssessment)
    evidence_index: list[EvidenceItem] = Field(default_factory=list)
    final_verdict: FinalVerdict = Field(default_factory=FinalVerdict)
    inconsistencies: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0, le=1)


class GitHubScoreBreakdown(RepositoryAnalyzerModel):
    """Final code-calculated scores on a 0..100 scale."""

    technical_score: int = Field(ge=0, le=100)
    portfolio_score: int = Field(ge=0, le=100)
    resume_evidence_score: int = Field(ge=0, le=100)
    recruiter_readiness_score: int = Field(ge=0, le=100)
    job_alignment_score: int = Field(ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)
    documentation_score: int = Field(ge=0, le=100)
    test_signal_score: int = Field(ge=0, le=100)
    security_score: int = Field(ge=0, le=100)
    security_risk_level: RiskLevel
    grade: Grade
    confidence_score: float = Field(ge=0, le=1)
    applied_caps: list[str] = Field(default_factory=list)


class GitHubAnalyzerReport(RepositoryAnalyzerModel):
    """Final SotuHire GitHub Analyzer 2 report."""

    repository_identity: RepositoryIdentityAssessment
    executive_summary: ExecutiveSummary
    dimension_scores: DimensionScores
    score_explanation: list[str] = Field(default_factory=list)
    tech_stack: TechStackAssessment
    architecture: ArchitectureAssessment
    security: SecurityAssessment
    documentation: list[str] = Field(default_factory=list)
    testing: list[str] = Field(default_factory=list)
    portfolio_value: PortfolioValueAssessment
    resume_evidence: ResumeEvidenceAssessment
    job_alignment: list[str] = Field(default_factory=list)
    inconsistencies: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    evidence_index: list[EvidenceItem] = Field(default_factory=list)
    files_sampled: list[str] = Field(default_factory=list)
    final_verdict: FinalVerdict
    scores: GitHubScoreBreakdown
    provider_used: str = "local"
    fallback_used: bool = False
