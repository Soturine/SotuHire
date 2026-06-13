"""Provider routing with a deterministic fallback."""

from __future__ import annotations

import importlib.util
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
    requested_provider: str
    fallback_used: bool = False
    warning: str = ""


def _configured_provider(name: str | None = None) -> str:
    return (
        (name or os.getenv("DEFAULT_AI_PROVIDER") or os.getenv("LLM_PROVIDER") or "local")
        .strip()
        .lower()
    )


def get_provider(name: str | None = None) -> AIProvider:
    """Create a supported provider from explicit or environment configuration."""
    provider_name = _configured_provider(name)
    if provider_name == "gemini":
        return GeminiProvider()
    return MockProvider()


def gemini_setup_warning(api_key: str | None = None) -> str:
    """Return a clear setup warning when Gemini cannot be selected yet."""
    if not (api_key or os.getenv("GEMINI_API_KEY", "")).strip():
        return "Gemini não configurado. Usando análise local."
    try:
        sdk_available = importlib.util.find_spec("google.genai") is not None
    except ModuleNotFoundError:
        sdk_available = False
    if not sdk_available:
        return "Instale requirements-ai.txt para usar Gemini."
    return ""


def _short_error(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    return message[:220] or exc.__class__.__name__


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
        return StructuredAnalysisResult(
            analysis=analysis,
            provider=selected.name,
            requested_provider=selected.name,
        )
    except Exception as exc:
        fallback = MockProvider()
        analysis = fallback.analyze(resume_text, job_text, preferences, job_details)
        return StructuredAnalysisResult(
            analysis=analysis,
            provider=fallback.name,
            requested_provider=selected.name,
            fallback_used=True,
            warning=(
                f"Gemini falhou: {_short_error(exc)} Provider usado: Análise local. Fallback usado."
            ),
        )
