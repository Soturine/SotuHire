"""Repository metadata and file models for GitHub Analyzer 2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepositoryAnalyzerModel(BaseModel):
    """Base model for GitHub Analyzer contracts."""

    model_config = ConfigDict(extra="forbid")


class RepositoryIdentity(RepositoryAnalyzerModel):
    """Stable public identity for a GitHub repository."""

    owner: str
    name: str
    url: str
    default_branch: str = ""
    ref_sha: str = ""


class RepositoryMetadata(RepositoryAnalyzerModel):
    """Public metadata collected from GitHub API."""

    identity: RepositoryIdentity
    description: str = ""
    topics: list[str] = Field(default_factory=list)
    languages: dict[str, int | float] = Field(default_factory=dict)
    stars: int | None = None
    forks: int | None = None
    license: str = ""
    created_at: str = ""
    updated_at: str = ""
    homepage: str = ""
    archived: bool = False
    fork: bool = False
    rate_limit_remaining: int | None = None


RepositoryTreeEntryType = Literal["blob", "tree", "commit", "unknown"]


class RepositoryTreeEntry(RepositoryAnalyzerModel):
    """Single entry in a repository tree."""

    path: str
    type: RepositoryTreeEntryType = "unknown"
    size: int | None = Field(default=None, ge=0)
    sha: str = ""
    url: str = ""


class RepositoryTree(RepositoryAnalyzerModel):
    """Repository tree plus GitHub truncation status."""

    entries: list[RepositoryTreeEntry] = Field(default_factory=list)
    truncated: bool = False
    ref: str = ""


EvidenceType = Literal[
    "file_presence",
    "code_content",
    "config",
    "readme",
    "workflow",
    "dependency",
    "tree",
    "metadata",
]


class RepositoryDetectedSignals(RepositoryAnalyzerModel):
    """Repository-level signals inferred from tree and selected files."""

    has_readme: bool = False
    has_tests: bool = False
    has_ci: bool = False
    has_docker: bool = False
    has_docs: bool = False
    has_license: bool = False
    has_env_example: bool = False
    has_package_manifest: bool = False
    has_security_policy: bool = False
    has_dependency_lock: bool = False
    has_large_files_skipped: bool = False
    tree_truncated: bool = False
    test_paths: list[str] = Field(default_factory=list)
    doc_paths: list[str] = Field(default_factory=list)
    workflow_paths: list[str] = Field(default_factory=list)
    manifest_paths: list[str] = Field(default_factory=list)
    security_paths: list[str] = Field(default_factory=list)
    skipped_paths: list[str] = Field(default_factory=list)


class SelectedRepositoryFile(RepositoryAnalyzerModel):
    """Repository file selected for content-aware analysis."""

    path: str
    content: str = ""
    reason_selected: str
    size: int | None = Field(default=None, ge=0)
    language_hint: str = ""
    fetched: bool = False
    truncated: bool = False


class RepositoryAnalysisInput(RepositoryAnalyzerModel):
    """Optional career context used to interpret repository evidence."""

    mode: Literal[
        "technical_quality",
        "portfolio_value",
        "resume_evidence",
        "job_alignment",
        "full",
    ] = "full"
    target_role: str = ""
    target_job: dict[str, object] = Field(default_factory=dict)
    candidate_profile: dict[str, object] = Field(default_factory=dict)
    career_domains: list[str] = Field(default_factory=list)
    language: str = "pt-BR"
