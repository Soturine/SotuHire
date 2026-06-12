"""Provider contract for structured job analysis."""

from __future__ import annotations

from abc import ABC, abstractmethod

from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class ProviderUnavailableError(RuntimeError):
    """Raised when an optional AI provider cannot be used."""


class AIProvider(ABC):
    """Provider-agnostic structured-analysis contract."""

    name: str

    @abstractmethod
    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
    ) -> JobAnalysisSchema:
        """Return a validated structured analysis."""
