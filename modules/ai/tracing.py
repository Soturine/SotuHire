"""Common secret-free trace recorder for AI task consumers outside analysis routes."""

from __future__ import annotations

import hashlib
import os
import time
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from modules.ai.task_registry import default_ai_task_registry
from modules.storage.ai_runs import AiRun, AiRunStore


def record_ai_run(
    task_id: str,
    *,
    provider_requested: str,
    provider_used: str,
    model_requested: str = "",
    model_used: str = "",
    fallback_used: bool = False,
    fallback_reason: str = "",
    schema_valid: bool = True,
    provider: object | None = None,
    started_at: datetime | None = None,
    started_monotonic: float | None = None,
    context_source_types: list[str] | None = None,
    context_item_count: int = 0,
    evidence_count: int = 0,
    source_refs: list[str] | None = None,
    warnings: list[str] | None = None,
    error_type: str = "",
    benchmark_run_id: str = "",
    parent_run_id: str = "",
) -> AiRun:
    """Build and optionally persist one task-owned trace without raw inputs or outputs."""
    task = default_ai_task_registry().get(task_id)
    metadata = getattr(provider, "last_call_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    now = datetime.now(UTC)
    latency_ms = metadata.get("latency_ms")
    if latency_ms is None and started_monotonic is not None:
        latency_ms = round((time.perf_counter() - started_monotonic) * 1000)
    refs = list(dict.fromkeys(value for value in source_refs or [] if value))
    input_hash = hashlib.sha256(
        "\x1f".join([task.task_id, *refs, parent_run_id]).encode("utf-8")
    ).hexdigest()
    used_model = model_used or ("local" if provider_used == "local" else model_requested)
    run = AiRun(
        task_id=task.task_id,
        feature=task.context_purpose,
        provider_requested=provider_requested,
        provider_used=provider_used,
        model_requested=model_requested or "local",
        model_used=used_model or "local",
        prompt_id=task.prompt_id,
        prompt_version=task.prompt_version,
        analysis_mode=(
            "fallback" if fallback_used else "local" if provider_used == "local" else "ai"
        ),
        input_hash=input_hash,
        input_schema_version=task.input_schema.rsplit("@", 1)[-1],
        output_schema_version=task.prompt_version,
        context_purpose=task.context_purpose,
        context_source_types=list(dict.fromkeys(context_source_types or [])),
        context_item_count=max(0, context_item_count),
        evidence_count=max(0, evidence_count),
        schema_valid=schema_valid,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        started_at=started_at or metadata.get("started_at") or now,
        finished_at=metadata.get("finished_at") or now,
        latency_ms=latency_ms,
        input_tokens=_optional_int(metadata.get("input_tokens")),
        output_tokens=_optional_int(metadata.get("output_tokens")),
        total_tokens=_optional_int(metadata.get("total_tokens")),
        estimated_cost=_optional_float(metadata.get("estimated_cost")),
        error_type=str(metadata.get("error_type") or error_type),
        error_message_sanitized=fallback_reason if fallback_used else "",
        source_refs=refs,
        warnings=warnings or [],
        needs_user_review=True,
        benchmark_run_id=benchmark_run_id,
        parent_run_id=parent_run_id,
    )
    if not (os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("SOTUHIRE_DATA_DIR")):
        with suppress(OSError, RuntimeError, ValueError):
            AiRunStore().save(run)
    return run


def runtime_model(runtime: object) -> str:
    """Resolve a model name from real or lightweight test runtimes."""
    model = getattr(runtime, "model", "")
    if isinstance(model, str) and model:
        return model
    provider_name = getattr(runtime, "provider_name", "local")
    return str(provider_name or "local")


def runtime_trace_kwargs(
    runtime: object,
    *,
    model_used: str = "",
    fallback_used: bool | None = None,
) -> dict[str, Any]:
    """Return trace kwargs compatible with production and mocked AI runtimes."""
    resolved_model = runtime_model(runtime)
    requested = getattr(runtime, "model_requested", resolved_model)
    started_at = getattr(runtime, "started_at", None)
    started_monotonic = getattr(runtime, "started_monotonic", None)
    return {
        "model_requested": str(requested or resolved_model),
        "model_used": model_used or resolved_model,
        "fallback_used": (
            bool(getattr(runtime, "fallback_used", False))
            if fallback_used is None
            else fallback_used
        ),
        "provider": getattr(runtime, "provider", None),
        "started_at": started_at if isinstance(started_at, datetime) else None,
        "started_monotonic": (
            float(started_monotonic) if isinstance(started_monotonic, int | float) else None
        ),
    }


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


__all__ = ["record_ai_run", "runtime_model", "runtime_trace_kwargs"]
