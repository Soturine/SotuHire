"""Registered consumers for cautious career, GitHub-profile and portfolio guidance."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.prompt_registry import PromptRegistry
from modules.ai.schemas.analysis_insights import SafeAiInsightOutput
from modules.ai.tracing import record_ai_run

GuidanceTask = Literal["career_advice", "github_profile_analysis", "portfolio_gap_analysis"]


class GuidanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output: SafeAiInsightOutput
    provider_used: str
    requested_provider: str
    fallback_used: bool = False
    run_id: str


_PROMPTS = {
    "career_advice": "career_advice_v1",
    "github_profile_analysis": "github_profile_analysis_v1",
    "portfolio_gap_analysis": "portfolio_gap_analysis_v1",
}


def generate_guidance(
    task_id: GuidanceTask,
    payload: dict[str, object],
    *,
    provider: Any | None = None,
    registry: PromptRegistry | None = None,
) -> GuidanceResult:
    """Run one registered guidance prompt with a cautious deterministic fallback."""
    requested = str(getattr(provider, "name", "local"))
    started_at = datetime.now(UTC)
    started_monotonic = time.perf_counter()
    prompt_registry = registry or default_prompt_registry()
    if provider is not None and requested != "local":
        try:
            output = SafeAiInsightOutput.model_validate(
                provider.generate_structured(prompt_registry.get(_PROMPTS[task_id]), payload)
            )
            trace = record_ai_run(
                task_id,
                provider_requested=requested,
                provider_used=requested,
                model_requested=str(getattr(provider, "model", "")),
                model_used=str(getattr(provider, "model", "")),
                provider=provider,
                started_at=started_at,
                started_monotonic=started_monotonic,
                warnings=output.warnings,
            )
            return GuidanceResult(
                output=output,
                provider_used=requested,
                requested_provider=requested,
                run_id=trace.run_id,
            )
        except Exception as exc:
            fallback = _local_guidance(task_id)
            trace = record_ai_run(
                task_id,
                provider_requested=requested,
                provider_used="local",
                model_requested=str(getattr(provider, "model", "")),
                model_used="local",
                fallback_used=True,
                fallback_reason="Provider indisponível; orientação local conservadora utilizada.",
                provider=provider,
                started_at=started_at,
                started_monotonic=started_monotonic,
                warnings=fallback.warnings,
                error_type=type(exc).__name__,
            )
            return GuidanceResult(
                output=fallback,
                provider_used="local",
                requested_provider=requested,
                fallback_used=True,
                run_id=trace.run_id,
            )
    fallback = _local_guidance(task_id)
    trace = record_ai_run(
        task_id,
        provider_requested=requested,
        provider_used="local",
        model_requested="local",
        model_used="local",
        started_at=started_at,
        started_monotonic=started_monotonic,
        warnings=fallback.warnings,
    )
    return GuidanceResult(
        output=fallback,
        provider_used="local",
        requested_provider=requested,
        run_id=trace.run_id,
    )


def _local_guidance(task_id: GuidanceTask) -> SafeAiInsightOutput:
    labels = {
        "career_advice": "Revise objetivos e evidências confirmadas antes de escolher a próxima ação.",
        "github_profile_analysis": "Revise somente evidências públicas dos repositórios selecionados.",
        "portfolio_gap_analysis": "Trate ausência de evidência como informação faltante, não como deficiência.",
    }
    return SafeAiInsightOutput(
        safe_actions=[labels[task_id]],
        warnings=["Fallback local não cria fatos nem altera o Perfil."],
        confidence=0.4,
    )


__all__ = ["GuidanceResult", "GuidanceTask", "generate_guidance"]
