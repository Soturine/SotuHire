"""Provider routing with a deterministic fallback."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from modules.ai.diagnostics import GeminiDiagnostic, diagnose_gemini_error
from modules.ai.providers import AIProvider, GeminiProvider, MockProvider
from modules.ai.setup import (
    default_ai_provider,
    gemini_key_source,
    gemini_model,
    gemini_setup_status,
)
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
    diagnostic: GeminiDiagnostic | None = None


def _configured_provider(name: str | None = None) -> str:
    return default_ai_provider(name)


def get_provider(name: str | None = None) -> AIProvider:
    """Create a supported provider from explicit or environment configuration."""
    provider_name = _configured_provider(name)
    if provider_name == "gemini":
        return GeminiProvider()
    return MockProvider()


def gemini_setup_warning(api_key: str | None = None) -> str:
    """Return a clear setup warning when Gemini cannot be selected yet."""
    status = gemini_setup_status(api_key)
    return "" if status.available else f"{status.message} Motivo: {status.reason}."


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
        diagnostic = diagnose_gemini_error(
            exc,
            test_type="analysis",
            model=getattr(selected, "model", gemini_model()),
            key_source=gemini_key_source(getattr(selected, "api_key", None)),
            call_type="generate_content com response_json_schema",
        )
        return StructuredAnalysisResult(
            analysis=analysis,
            provider=fallback.name,
            requested_provider=selected.name,
            fallback_used=True,
            warning=(
                "Gemini falhou, então usei análise local. "
                f"Motivo: {diagnostic.summary}. "
                f"Código: {diagnostic.code or 'não informado'}. "
                "Provider usado: Análise local. Fallback usado: Sim."
            ),
            diagnostic=diagnostic,
        )
