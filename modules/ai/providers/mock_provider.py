"""Deterministic provider used by default and in automated tests."""

from __future__ import annotations

from modules.ai.providers.base import AIProvider
from modules.analyzer.job_analyzer import analyze_job
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class MockProvider(AIProvider):
    """Use the local analyzer while preserving the provider interface."""

    name = "mock"

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
    ) -> JobAnalysisSchema:
        """Return deterministic output with the production schema."""
        return analyze_job(resume_text, job_text, preferences, job_details)
