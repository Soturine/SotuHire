"""Provider routing with a deterministic fallback."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from modules.ai.diagnostics import GeminiDiagnostic, diagnose_gemini_error
from modules.ai.providers import AIProvider, GeminiProvider, MockProvider
from modules.ai.setup import (
    default_ai_provider,
    gemini_key_source,
    gemini_model,
    gemini_setup_status,
)
from modules.memory.memory_summarizer import summarize_evidence
from modules.memory.schemas import CareerEvidence
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class StructuredAnalysisResult(BaseModel):
    """Analysis plus provider-routing metadata."""

    model_config = ConfigDict(extra="forbid")

    analysis: JobAnalysisSchema
    provider: str
    requested_provider: str
    fallback_used: bool = False
    model: str = ""
    warning: str = ""
    diagnostic: GeminiDiagnostic | None = None
    evidence: list[CareerEvidence] = Field(default_factory=list)
    memory_used: bool = False
    memory_shared_with_provider: bool = False


def _configured_provider(name: str | None = None) -> str:
    return default_ai_provider(name)


def get_provider(
    name: str | None = None,
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> AIProvider:
    """Create a supported provider from explicit or environment configuration."""
    provider_name = _configured_provider(name)
    if provider_name == "gemini":
        return GeminiProvider(api_key=api_key, model=model)
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
    memory_evidence: list[CareerEvidence] | None = None,
    share_memory_with_provider: bool = False,
) -> StructuredAnalysisResult:
    """Run structured analysis and fall back locally if an optional provider fails."""
    selected = provider or get_provider()
    evidence = memory_evidence or []
    memory_context = summarize_evidence(evidence)
    provider_memory_context = (
        memory_context
        if selected.name == "local" or (selected.name == "gemini" and share_memory_with_provider)
        else ""
    )
    try:
        analysis = _run_provider_analysis(
            selected=selected,
            resume_text=resume_text,
            job_text=job_text,
            preferences=preferences,
            job_details=job_details,
            memory_context=provider_memory_context,
        )
        analysis = _enhance_with_match_engine_v2(
            analysis,
            resume_text=resume_text,
            job_text=job_text,
            preferences=preferences,
            job_details=job_details,
            memory_context=memory_context,
        )
        return StructuredAnalysisResult(
            analysis=analysis,
            provider=selected.name,
            requested_provider=selected.name,
            model=getattr(selected, "model", ""),
            evidence=evidence,
            memory_used=bool(evidence),
            memory_shared_with_provider=bool(
                evidence and selected.name == "gemini" and share_memory_with_provider
            ),
        )
    except Exception as exc:
        fallback = MockProvider()
        analysis = fallback.analyze(
            resume_text,
            job_text,
            preferences,
            job_details,
            memory_context=memory_context,
        )
        analysis = _enhance_with_match_engine_v2(
            analysis,
            resume_text=resume_text,
            job_text=job_text,
            preferences=preferences,
            job_details=job_details,
            memory_context=memory_context,
        )
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
            model=getattr(selected, "model", ""),
            warning=(
                "Gemini falhou, então usei análise local. "
                f"Motivo: {diagnostic.summary}. "
                f"Código: {diagnostic.code or 'não informado'}. "
                "Provider usado: Análise local. Fallback usado: Sim."
            ),
            diagnostic=diagnostic,
            evidence=evidence,
            memory_used=bool(evidence),
            memory_shared_with_provider=False,
        )


def _run_provider_analysis(
    *,
    selected: AIProvider,
    resume_text: str,
    job_text: str,
    preferences: UserPreferences | None,
    job_details: dict[str, object] | None,
    memory_context: str,
) -> JobAnalysisSchema:
    """Use the prompt registry when structured generation is available."""
    if selected.name != "local":
        try:
            from modules.ai.prompt_loader import default_prompt_registry

            spec = default_prompt_registry().get("match_analysis_evidence_based_v1")
            output = selected.generate_structured(
                spec,
                {
                    "resume_text": resume_text,
                    "job_text": job_text,
                    "preferences": (preferences or UserPreferences()).model_dump(mode="json"),
                    "job_details": job_details or {},
                    "memory_context": memory_context,
                    "language": "pt-BR",
                },
            )
            return JobAnalysisSchema.model_validate(output)
        except Exception:
            # Let the caller handle diagnostics and deterministic fallback.
            raise
    return selected.analyze(
        resume_text,
        job_text,
        preferences,
        job_details,
        memory_context=memory_context,
    )


def _enhance_with_match_engine_v2(
    analysis: JobAnalysisSchema,
    *,
    resume_text: str,
    job_text: str,
    preferences: UserPreferences | None,
    job_details: dict[str, object] | None,
    memory_context: str,
) -> JobAnalysisSchema:
    """Use Match Engine 2 locally when structured extraction can be built safely."""
    try:
        from modules.ai.structured_job_extractor import extract_structured_job
        from modules.ai.structured_resume_extractor import extract_structured_resume
        from modules.analyzer.job_analyzer import analyze_job_v2

        local_provider = MockProvider()
        resume = extract_structured_resume(resume_text, provider=local_provider).output
        job = extract_structured_job(job_text, provider=local_provider).output
        memory_items = [memory_context] if memory_context.strip() else []
        return analyze_job_v2(
            resume=resume,
            job=job,
            memory_items=memory_items,
            preferences_fit_score=analysis.opportunity_fit_score,
            fallback_resume_text=resume_text,
            fallback_job_text=job_text,
        )
    except Exception:
        return analysis
