"""Exceptions for the GitHub Analyzer 2 pipeline."""

from __future__ import annotations


class GitHubAnalyzerError(RuntimeError):
    """Base error for repository analysis failures."""


class GitHubUrlError(GitHubAnalyzerError, ValueError):
    """Raised when a GitHub URL cannot be resolved to owner/repo."""


class GitHubApiError(GitHubAnalyzerError):
    """Raised when GitHub API or raw content requests fail."""


class GitHubAnalysisUnavailable(GitHubAnalyzerError):
    """Raised when a full analysis cannot be produced from available evidence."""
