"""Secret-free execution metadata for auditable AI-assisted features."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database


def utc_now() -> datetime:
    return datetime.now(UTC)


class AiTraceSettings(BaseModel):
    """Safe trace retention/content policy loaded from environment variables."""

    model_config = ConfigDict(extra="forbid")

    ai_trace_retention_days: int = Field(default=90, ge=1, le=3650)
    ai_trace_store_inputs: bool = False
    ai_trace_store_outputs: bool = False
    ai_trace_store_redacted_excerpts: bool = True

    @classmethod
    def from_env(cls) -> AiTraceSettings:
        return cls(
            ai_trace_retention_days=_env_int("AI_TRACE_RETENTION_DAYS", 90),
            ai_trace_store_inputs=_env_bool("AI_TRACE_STORE_INPUTS", False),
            ai_trace_store_outputs=_env_bool("AI_TRACE_STORE_OUTPUTS", False),
            ai_trace_store_redacted_excerpts=_env_bool("AI_TRACE_STORE_REDACTED_EXCERPTS", True),
        )


class AiRun(BaseModel):
    """Safe AI trace; prompts, responses, personal context and secrets are excluded."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(default_factory=lambda: uuid4().hex)
    task_id: str = ""
    feature: str
    provider_requested: str = "local"
    provider_used: str = "local"
    model_requested: str = "local"
    model_used: str = "local"
    prompt_id: str = ""
    prompt_version: str = ""
    analysis_mode: Literal["local", "ai", "fallback"] = "local"
    input_hash: str = ""
    input_schema_version: str = "1"
    output_schema_version: str = "1"
    context_purpose: str = ""
    context_source_types: list[str] = Field(default_factory=list)
    context_item_count: int = Field(default=0, ge=0)
    evidence_count: int = Field(default=0, ge=0)
    schema_valid: bool = True
    fallback_used: bool = False
    fallback_reason: str = ""
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime = Field(default_factory=utc_now)
    latency_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    error_type: str = ""
    error_message_sanitized: str = ""
    warnings: list[str] = Field(default_factory=list)
    needs_user_review: bool = True
    benchmark_run_id: str = ""
    parent_run_id: str = ""
    # v1.9.6 compatibility fields; only safe identifiers are retained.
    token_usage: dict[str, int] = Field(default_factory=dict)
    context_sources: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_used: list[dict[str, Any] | str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def normalize_metadata(self) -> AiRun:
        usage = dict(self.token_usage)
        self.input_tokens = (
            self.input_tokens if self.input_tokens is not None else usage.get("input")
        )
        self.output_tokens = (
            self.output_tokens if self.output_tokens is not None else usage.get("output")
        )
        if self.total_tokens is None:
            self.total_tokens = usage.get("total")
        if self.total_tokens is None and (
            self.input_tokens is not None or self.output_tokens is not None
        ):
            self.total_tokens = (self.input_tokens or 0) + (self.output_tokens or 0)
        self.token_usage = {
            key: value
            for key, value in {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "total": self.total_tokens,
            }.items()
            if value is not None
        }
        self.error_message_sanitized = sanitize_error_message(self.error_message_sanitized)
        self.warnings = [sanitize_error_message(value) for value in self.warnings]
        self.fallback_reason = sanitize_error_message(self.fallback_reason)
        self.source_refs = [_safe_ref(value) for value in self.source_refs if _safe_ref(value)]
        return self


class AiRunStore:
    """Persist, paginate and expire AI metadata without storing credentials or full content."""

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        settings: AiTraceSettings | None = None,
    ) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )
        self.settings = settings or AiTraceSettings.from_env()

    def save(self, run: AiRun) -> AiRun:
        safe_run = run.model_copy(
            update={
                "evidence_used": _redacted_evidence(run.evidence_used)
                if self.settings.ai_trace_store_redacted_excerpts
                else [],
            }
        )
        serialized = safe_run.model_dump(mode="json")
        if any(_looks_secret(value) for value in _strings(serialized)):
            raise ValueError("AiRun contém material com aparência de segredo.")
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO ai_runs
                (run_id, task_id, feature, provider_requested, provider_used, model_requested,
                 model_used, prompt_id, prompt_version, analysis_mode, input_hash,
                 input_schema_version, output_schema_version, context_purpose,
                 context_source_types, context_item_count, evidence_count, schema_valid,
                 fallback_used, fallback_reason, started_at, finished_at, latency_ms,
                 input_tokens, output_tokens, total_tokens, estimated_cost, error_type,
                 error_message_sanitized, warnings, needs_user_review, benchmark_run_id,
                 parent_run_id, token_usage, context_sources, source_refs, evidence_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    safe_run.run_id,
                    safe_run.task_id,
                    safe_run.feature,
                    safe_run.provider_requested,
                    safe_run.provider_used,
                    safe_run.model_requested,
                    safe_run.model_used,
                    safe_run.prompt_id,
                    safe_run.prompt_version,
                    safe_run.analysis_mode,
                    safe_run.input_hash,
                    safe_run.input_schema_version,
                    safe_run.output_schema_version,
                    safe_run.context_purpose,
                    _json(safe_run.context_source_types),
                    safe_run.context_item_count,
                    safe_run.evidence_count,
                    int(safe_run.schema_valid),
                    int(safe_run.fallback_used),
                    safe_run.fallback_reason,
                    safe_run.started_at.isoformat(),
                    safe_run.finished_at.isoformat(),
                    safe_run.latency_ms,
                    safe_run.input_tokens,
                    safe_run.output_tokens,
                    safe_run.total_tokens,
                    safe_run.estimated_cost,
                    safe_run.error_type,
                    safe_run.error_message_sanitized,
                    _json(safe_run.warnings),
                    int(safe_run.needs_user_review),
                    safe_run.benchmark_run_id,
                    safe_run.parent_run_id,
                    _json(safe_run.token_usage),
                    _json(safe_run.context_sources),
                    _json(safe_run.source_refs),
                    _json(safe_run.evidence_used),
                    safe_run.created_at.isoformat(),
                ),
            )
        return safe_run

    def get(self, run_id: str) -> AiRun | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT * FROM ai_runs WHERE run_id = ?", (run_id,)).fetchone()
        return _from_row(row) if row is not None else None

    def list(
        self,
        *,
        feature: str = "",
        task_id: str = "",
        provider: str = "",
        benchmark_run_id: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[AiRun]:
        ensure_database(self.database_path)
        clauses: list[str] = []
        parameters: list[object] = []
        for column, value in (
            ("feature", feature),
            ("task_id", task_id),
            ("provider_used", provider),
            ("benchmark_run_id", benchmark_run_id),
        ):
            if value:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        query = "SELECT * FROM ai_runs"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY started_at DESC, created_at DESC LIMIT ? OFFSET ?"
        parameters.extend([max(1, min(limit, 500)), max(0, offset)])
        with connect_database(self.database_path) as connection:
            rows = connection.execute(query, tuple(parameters)).fetchall()
        return [_from_row(row) for row in rows]

    def count(self) -> int:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            return int(connection.execute("SELECT COUNT(*) FROM ai_runs").fetchone()[0])

    def purge_expired(self, *, now: datetime | None = None) -> int:
        ensure_database(self.database_path)
        cutoff = (now or utc_now()) - timedelta(days=self.settings.ai_trace_retention_days)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM ai_runs WHERE COALESCE(NULLIF(finished_at, ''), created_at) < ?",
                (cutoff.isoformat(),),
            )
        return int(cursor.rowcount)


def sanitize_error_message(value: str) -> str:
    """Redact credentials, headers and long opaque values from stored diagnostics."""
    text = str(value or "")[:1000]
    text = re.sub(r"AIza[0-9A-Za-z_-]{12,}", "[REDACTED]", text)
    text = re.sub(r"sk-(?:proj-)?[0-9A-Za-z_-]{12,}", "[REDACTED]", text)
    text = re.sub(r"(?i)(authorization\s*[:=]\s*)([^\s,;]+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(api[_ -]?key\s*[:=]\s*)([^\s,;]+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(bearer\s+)([^\s,;]+)", r"\1[REDACTED]", text)
    return " ".join(text.split())


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _looks_secret(value: str) -> bool:
    lowered = value.casefold()
    if any(marker in lowered for marker in ("authorization:", "bearer ")):
        return True
    return bool(
        re.search(r"\bAIza[0-9A-Za-z_-]{20,}\b", value)
        or re.search(r"\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}\b", value)
    )


def _redacted_evidence(values: list[dict[str, Any] | str]) -> list[dict[str, Any] | str]:
    redacted: list[dict[str, Any] | str] = []
    for value in values[:100]:
        if isinstance(value, str):
            redacted.append({"ref": _safe_ref(value)})
            continue
        redacted.append(
            {
                key: item
                for key, item in value.items()
                if key in {"id", "kind", "source", "source_ref", "confirmed_by_user"}
                and isinstance(item, (str, bool, int, float, type(None)))
            }
        )
    return redacted


def _safe_ref(value: str) -> str:
    text = str(value or "").strip()[:500]
    if not text:
        return ""
    try:
        parts = urlsplit(text)
    except ValueError:
        return sanitize_error_message(text)
    if parts.scheme and parts.netloc:
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return sanitize_error_message(text)


def _from_row(row: Any) -> AiRun:
    keys = set(row.keys())

    def value(name: str, default: Any = "") -> Any:
        return row[name] if name in keys else default

    usage = _load_json(value("token_usage", "{}"), {})
    context_sources = _load_json(value("context_sources", "[]"), [])
    return AiRun(
        run_id=row["run_id"],
        task_id=value("task_id"),
        feature=row["feature"],
        provider_requested=row["provider_requested"],
        provider_used=row["provider_used"],
        model_requested=row["model_requested"],
        model_used=row["model_used"],
        prompt_id=row["prompt_id"],
        prompt_version=row["prompt_version"],
        analysis_mode=row["analysis_mode"],
        input_hash=row["input_hash"],
        input_schema_version=value("input_schema_version", "1"),
        output_schema_version=value("output_schema_version", "1"),
        context_purpose=value("context_purpose"),
        context_source_types=_load_json(value("context_source_types", "[]"), context_sources),
        context_item_count=int(value("context_item_count", len(context_sources))),
        evidence_count=int(value("evidence_count", 0)),
        schema_valid=bool(row["schema_valid"]),
        fallback_used=bool(row["fallback_used"]),
        fallback_reason=row["fallback_reason"],
        started_at=value("started_at") or row["created_at"],
        finished_at=value("finished_at") or row["created_at"],
        latency_ms=row["latency_ms"],
        input_tokens=value("input_tokens", usage.get("input")),
        output_tokens=value("output_tokens", usage.get("output")),
        total_tokens=value("total_tokens", usage.get("total")),
        estimated_cost=row["estimated_cost"],
        error_type=value("error_type"),
        error_message_sanitized=value("error_message_sanitized"),
        warnings=_load_json(row["warnings"], []),
        needs_user_review=bool(row["needs_user_review"]),
        benchmark_run_id=value("benchmark_run_id"),
        parent_run_id=value("parent_run_id"),
        token_usage=usage,
        context_sources=context_sources,
        source_refs=_load_json(row["source_refs"], []),
        evidence_used=_load_json(row["evidence_used"], []),
        created_at=row["created_at"],
    )


def _load_json(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(f"SOTUHIRE_{name}", os.getenv(name.casefold(), ""))
    if not value:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(f"SOTUHIRE_{name}", os.getenv(name.casefold(), ""))
    try:
        return int(value) if value else default
    except ValueError:
        return default


__all__ = ["AiRun", "AiRunStore", "AiTraceSettings", "sanitize_error_message"]
