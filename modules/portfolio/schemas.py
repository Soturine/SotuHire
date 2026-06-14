"""Typed contracts for GitHub, repository, project, and portfolio analysis."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

ProjectPageType = Literal["github_profile", "github_repo", "portfolio", "project"]


class ProjectAnalysisPayload(BaseModel):
    """Public project information captured by the extension or entered in SotuHire."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(max_length=2048)
    owner: str = Field(default="", max_length=200)
    repo: str = Field(default="", max_length=200)
    title: str = Field(default="", max_length=500)
    page_type: ProjectPageType = "project"
    visible_text: str = Field(default="", max_length=200_000)
    readme_text: str = Field(default="", max_length=100_000)
    files_sampled: list[str] = Field(default_factory=list, max_length=200)
    commit_messages: list[str] = Field(default_factory=list, max_length=200)
    languages: list[str] = Field(default_factory=list, max_length=100)
    topics: list[str] = Field(default_factory=list, max_length=100)
    analysis_result: dict[str, object] = Field(default_factory=dict)
    provider_used: str = Field(default="local", max_length=50)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("O projeto deve usar uma URL HTTP ou HTTPS.")
        return value


class CommitAnalysis(BaseModel):
    """Deterministic summary of recent public commit messages."""

    model_config = ConfigDict(extra="forbid")

    commit_quality_score: int = Field(ge=0, le=100)
    maintenance_signal_score: int = Field(ge=0, le=100)
    professionalism_score: int = Field(ge=0, le=100)
    conventional_ratio: float = Field(ge=0, le=1)
    generic_messages: list[str] = Field(default_factory=list)
    relevant_messages: list[str] = Field(default_factory=list)


class ProjectAnalysisReport(BaseModel):
    """Full report shared by standalone extension and connected SotuHire mode."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    url: str
    title: str = ""
    owner: str = ""
    repo: str = ""
    page_type: ProjectPageType
    provider_used: str = "local"
    overall_score: int = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "F"]
    github_profile_score: int = Field(ge=0, le=100)
    repository_quality_score: int = Field(ge=0, le=100)
    portfolio_score: int = Field(ge=0, le=100)
    project_quality_score: int = Field(ge=0, le=100)
    recruiter_readiness_score: int = Field(ge=0, le=100)
    documentation_score: int = Field(ge=0, le=100)
    commit_quality_score: int = Field(ge=0, le=100)
    architecture_signal_score: int = Field(ge=0, le=100)
    technical_depth_score: int = Field(ge=0, le=100)
    ats_job_evidence_score: int = Field(ge=0, le=100)
    summary: str = ""
    stack: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    relevant_projects: list[str] = Field(default_factory=list)
    improvement_projects: list[str] = Field(default_factory=list)
    priority_recommendations: list[str] = Field(default_factory=list)
    technical_keywords: list[str] = Field(default_factory=list)
    resume_highlights: list[str] = Field(default_factory=list)
    files_sampled: list[str] = Field(default_factory=list)
    commit_analysis: CommitAnalysis
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectAnalysisRecord(BaseModel):
    """Locally persisted payload and report."""

    model_config = ConfigDict(extra="forbid")

    payload: ProjectAnalysisPayload
    report: ProjectAnalysisReport
