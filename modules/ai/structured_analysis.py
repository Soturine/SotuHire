"""Provider routing with a deterministic fallback."""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict

from modules.ai.providers import AIProvider, GeminiProvider, MockProvider
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class StructuredAnalysisResult(BaseModel):
    """Analysis plus provider-routing metadata."""

    model_config = ConfigDict(extra="forbid")

    analysis: JobAnalysisSchema
    provider: str
    fallback_used: bool = False
    warning: str = ""


def get_provider(name: str | None = None) -> AIProvider:
    """Create a supported provider from explicit or environment configuration."""
    provider_name = (name or os.getenv("DEFAULT_AI_PROVIDER", "mock")).strip().lower()
    if provider_name == "gemini":
        return GeminiProvider()
    return MockProvider()


def analyze_structured(
    resume_text: str,
    job_text: str,
    preferences: UserPreferences | None = None,
    job_details: dict[str, object] | None = None,
    provider: AIProvider | None = None,
) -> StructuredAnalysisResult:
    """Run structured analysis and fall back locally if an optional provider fails."""
    selected = provider or get_provider()
    try:
        analysis = selected.analyze(resume_text, job_text, preferences, job_details)
        return StructuredAnalysisResult(analysis=analysis, provider=selected.name)
    except Exception as exc:
        fallback = MockProvider()
        analysis = fallback.analyze(resume_text, job_text, preferences, job_details)
        return StructuredAnalysisResult(
            analysis=analysis,
            provider=fallback.name,
            fallback_used=True,
            warning=f"{selected.name} indisponivel; fallback local usado: {exc}",
        )
