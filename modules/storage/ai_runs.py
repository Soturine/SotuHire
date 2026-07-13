"""Secret-free execution metadata for auditable AI-assisted features."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database


class AiRun(BaseModel):
    """Safe AI trace; prompts and provider secrets are deliberately excluded."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(default_factory=lambda: uuid4().hex)
    feature: str
    provider_requested: str = "local"
    provider_used: str = "local"
    model_requested: str = "local"
    model_used: str = "local"
    prompt_id: str = ""
    prompt_version: str = ""
    analysis_mode: Literal["local", "ai", "fallback"] = "local"
    fallback_used: bool = False
    fallback_reason: str = ""
    schema_valid: bool = True
    latency_ms: int | None = Field(default=None, ge=0)
    token_usage: dict[str, int] = Field(default_factory=dict)
    estimated_cost: float | None = Field(default=None, ge=0)
    input_hash: str = ""
    context_sources: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_used: list[dict[str, Any] | str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    needs_user_review: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AiRunStore:
    """Persist and query AI run metadata without storing credentials."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save(self, run: AiRun) -> AiRun:
        serialized = run.model_dump(mode="json")
        if any(_looks_secret(value) for value in _strings(serialized)):
            raise ValueError("AiRun contém material com aparência de segredo.")
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO ai_runs
                (run_id, feature, provider_requested, provider_used, model_requested,
                 model_used, prompt_id, prompt_version, analysis_mode, fallback_used,
                 fallback_reason, schema_valid, latency_ms, token_usage, estimated_cost,
                 input_hash, context_sources, source_refs, evidence_used, warnings,
                 needs_user_review, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run.run_id,
                    run.feature,
                    run.provider_requested,
                    run.provider_used,
                    run.model_requested,
                    run.model_used,
                    run.prompt_id,
                    run.prompt_version,
                    run.analysis_mode,
                    int(run.fallback_used),
                    run.fallback_reason,
                    int(run.schema_valid),
                    run.latency_ms,
                    _json(run.token_usage),
                    run.estimated_cost,
                    run.input_hash,
                    _json(run.context_sources),
                    _json(run.source_refs),
                    _json(run.evidence_used),
                    _json(run.warnings),
                    int(run.needs_user_review),
                    run.created_at.isoformat(),
                ),
            )
        return run

    def list(self, *, feature: str = "", limit: int = 100) -> list[AiRun]:
        ensure_database(self.database_path)
        query = "SELECT * FROM ai_runs"
        parameters: tuple[object, ...]
        if feature:
            query += " WHERE feature = ?"
            parameters = (feature, limit)
        else:
            parameters = (limit,)
        query += " ORDER BY created_at DESC LIMIT ?"
        with connect_database(self.database_path) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [_from_row(row) for row in rows]


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
    if any(marker in lowered for marker in ("api_key", "apikey", "authorization", "bearer ")):
        return True
    return bool(
        re.search(r"\bAIza[0-9A-Za-z_-]{20,}\b", value)
        or re.search(r"\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}\b", value)
    )


def _from_row(row: Any) -> AiRun:
    return AiRun(
        run_id=row["run_id"],
        feature=row["feature"],
        provider_requested=row["provider_requested"],
        provider_used=row["provider_used"],
        model_requested=row["model_requested"],
        model_used=row["model_used"],
        prompt_id=row["prompt_id"],
        prompt_version=row["prompt_version"],
        analysis_mode=row["analysis_mode"],
        fallback_used=bool(row["fallback_used"]),
        fallback_reason=row["fallback_reason"],
        schema_valid=bool(row["schema_valid"]),
        latency_ms=row["latency_ms"],
        token_usage=json.loads(row["token_usage"]),
        estimated_cost=row["estimated_cost"],
        input_hash=row["input_hash"],
        context_sources=json.loads(row["context_sources"]),
        source_refs=json.loads(row["source_refs"]),
        evidence_used=json.loads(row["evidence_used"]),
        warnings=json.loads(row["warnings"]),
        needs_user_review=bool(row["needs_user_review"]),
        created_at=row["created_at"],
    )
