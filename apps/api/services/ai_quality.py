"""Read-only quality aggregates plus explicit human feedback writes."""

from __future__ import annotations

import os
from collections import defaultdict
from statistics import mean
from typing import Any

from modules.ai.benchmark_store import AiBenchmarkStore
from modules.ai.evaluation.metrics import (
    human_acceptance_rate,
    human_edit_rate,
    human_rejection_rate,
)
from modules.ai.feedback import AiFeedback, AiFeedbackStore
from modules.ai.task_registry import default_ai_task_registry
from modules.outcomes import sample_confidence
from modules.storage.ai_runs import AiRunStore

from apps.api.schemas.ai_quality import (
    AiFeedbackCreate,
    AiFeedbackPage,
    AiQualityCollection,
    AiQualitySummary,
    AiRunsPage,
)


def quality_summary() -> AiQualitySummary:
    runs = AiRunStore().list(limit=500)
    feedback = AiFeedbackStore().list(limit=500)
    if not runs:
        return AiQualitySummary()
    decisions = [item.decision for item in feedback]
    latencies = [item.latency_ms for item in runs if item.latency_ms is not None]
    return AiQualitySummary(
        executions=len(runs),
        schema_validity=sum(item.schema_valid for item in runs) / len(runs),
        fallback_rate=sum(item.fallback_used for item in runs) / len(runs),
        average_latency_ms=mean(latencies) if latencies else None,
        total_tokens=sum(item.total_tokens or 0 for item in runs),
        estimated_cost=(
            sum(item.estimated_cost or 0 for item in runs)
            if any(item.estimated_cost is not None for item in runs)
            else None
        ),
        human_acceptance_rate=human_acceptance_rate(decisions) if decisions else None,
        human_edit_rate=human_edit_rate(decisions) if decisions else None,
        human_rejection_rate=human_rejection_rate(decisions) if decisions else None,
        unsupported_claim_rate=(
            sum(item.unsupported_claim for item in feedback) / len(feedback) if feedback else None
        ),
        sample_confidence=sample_confidence(len(runs)),
        empty_state=False,
        message="Métricas descritivas; compare providers somente com amostra suficiente.",
    )


def quality_runs(
    *,
    task_id: str = "",
    provider: str = "",
    limit: int = 50,
    offset: int = 0,
) -> AiRunsPage:
    store = AiRunStore()
    return AiRunsPage(
        items=store.list(task_id=task_id, provider=provider, limit=limit, offset=offset),
        total=store.count(),
        limit=max(1, min(limit, 500)),
        offset=max(0, offset),
    )


def quality_providers() -> AiQualityCollection:
    runs = AiRunStore().list(limit=500)
    feedback = AiFeedbackStore().list(limit=500)
    decisions_by_run = {item.run_id: item.decision for item in feedback}
    unsupported_by_run = {item.run_id: item.unsupported_claim for item in feedback}
    grouped: dict[tuple[str, str, str], list[Any]] = defaultdict(list)
    for run in runs:
        grouped[(run.task_id or run.feature, run.provider_used, run.model_used)].append(run)
    items: list[dict[str, Any]] = []
    for (task_id, provider, model), selected in sorted(grouped.items()):
        latencies = [item.latency_ms for item in selected if item.latency_ms is not None]
        decisions = [
            decisions_by_run[item.run_id] for item in selected if item.run_id in decisions_by_run
        ]
        unsupported = [
            unsupported_by_run[item.run_id]
            for item in selected
            if item.run_id in unsupported_by_run
        ]
        quality = sum(item.schema_valid for item in selected) / len(selected)
        if unsupported:
            quality *= 1 - (sum(unsupported) / len(unsupported))
        items.append(
            {
                "task": task_id,
                "provider": provider,
                "model": model,
                "sample_size": len(selected),
                "sample_confidence": sample_confidence(len(selected)),
                "quality": round(quality, 4),
                "latency_ms": round(mean(latencies), 2) if latencies else None,
                "cost": (
                    round(sum(item.estimated_cost or 0 for item in selected), 8)
                    if any(item.estimated_cost is not None for item in selected)
                    else None
                ),
                "fallback_rate": sum(item.fallback_used for item in selected) / len(selected),
                "acceptance_rate": human_acceptance_rate(decisions) if decisions else None,
            }
        )
    return AiQualityCollection(items=items)


def quality_prompts() -> AiQualityCollection:
    runs = AiRunStore().list(limit=500)
    count_by_prompt: dict[tuple[str, str], int] = defaultdict(int)
    for run in runs:
        count_by_prompt[(run.prompt_id, run.prompt_version)] += 1
    items = []
    for task in default_ai_task_registry().list():
        items.append(
            {
                "task_id": task.task_id,
                "prompt_id": task.prompt_id,
                "prompt_version": task.prompt_version,
                "evaluation_suite": task.evaluation_suite,
                "providers_supported": list(task.providers_supported),
                "run_count": count_by_prompt[(task.prompt_id, task.prompt_version)],
                "baseline_status": "available" if task.evaluation_suite else "pending",
            }
        )
    return AiQualityCollection(items=items)


def quality_benchmarks(*, limit: int = 50, offset: int = 0) -> AiQualityCollection:
    database = os.getenv("SOTUHIRE_BENCHMARK_DATABASE", "benchmarks/ai-quality.db")
    return AiQualityCollection(
        items=AiBenchmarkStore(database).list_runs(limit=limit, offset=offset)
    )


def create_feedback(payload: AiFeedbackCreate) -> AiFeedback:
    return AiFeedbackStore().save(payload.to_record())


def list_feedback(
    *, run_id: str = "", task_id: str = "", limit: int = 50, offset: int = 0
) -> AiFeedbackPage:
    return AiFeedbackPage(
        items=AiFeedbackStore().list(run_id=run_id, task_id=task_id, limit=limit, offset=offset),
        limit=max(1, min(limit, 500)),
        offset=max(0, offset),
    )


def delete_feedback(feedback_id: str) -> bool:
    return AiFeedbackStore().delete(feedback_id)


__all__ = [
    "create_feedback",
    "delete_feedback",
    "list_feedback",
    "quality_benchmarks",
    "quality_prompts",
    "quality_providers",
    "quality_runs",
    "quality_summary",
]
