"""Deterministic local provider used by default and in automated tests."""

from __future__ import annotations

from modules.ai.providers.base import AIProvider
from modules.analyzer.job_analyzer import analyze_job
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class MockProvider(AIProvider):
    """Use the local analyzer while preserving the provider interface."""

    name = "local"

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
        memory_context: str = "",
    ) -> JobAnalysisSchema:
        """Return deterministic output with the production schema."""
        evidence_backed_resume = (
            f"{resume_text}\n\nEVIDÊNCIAS DA MEMÓRIA LOCAL:\n{memory_context}"
            if memory_context.strip()
            else resume_text
        )
        return analyze_job(evidence_backed_resume, job_text, preferences, job_details)
