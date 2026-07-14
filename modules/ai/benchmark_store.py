"""Persistence for sanitized benchmark metadata and per-case metrics."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.database import connect_database
from modules.storage.migrations import MigrationRunner


class AiBenchmark(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benchmark_run_id: str = Field(default_factory=lambda: uuid4().hex)
    git_sha: str = ""
    app_version: str
    suite: str
    providers: list[str]
    models: list[str] = Field(default_factory=list)
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    seed: int
    dataset_version: str
    environment: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    status: Literal["running", "completed", "failed"] = "running"


class AiBenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str = Field(default_factory=lambda: uuid4().hex)
    benchmark_run_id: str
    case_id: str
    task_id: str
    domain: str
    provider: str
    model: str = ""
    prompt_id: str
    prompt_version: str
    metrics: dict[str, float | int | bool | None]
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    fallback_used: bool = False
    schema_valid: bool = False
    error_type: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AiBenchmarkStore:
    """Use a dedicated benchmark database so personal data is never required."""

    def __init__(self, database_path: str | Path = "benchmarks/ai-quality.db") -> None:
        self.database_path = Path(database_path)

    def prepare(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        MigrationRunner(self.database_path).apply(create_backup=self.database_path.exists())

    def save_run(self, run: AiBenchmark) -> AiBenchmark:
        self.prepare()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO ai_benchmarks
                (benchmark_run_id, git_sha, app_version, suite, providers, models,
                 prompt_versions, seed, dataset_version, environment, started_at,
                 finished_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(benchmark_run_id) DO UPDATE SET
                    finished_at=excluded.finished_at, status=excluded.status""",
                (
                    run.benchmark_run_id,
                    run.git_sha,
                    run.app_version,
                    run.suite,
                    _json(run.providers),
                    _json(run.models),
                    _json(run.prompt_versions),
                    run.seed,
                    run.dataset_version,
                    run.environment,
                    run.started_at.isoformat(),
                    run.finished_at.isoformat() if run.finished_at else "",
                    run.status,
                ),
            )
        return run

    def save_result(self, result: AiBenchmarkResult) -> AiBenchmarkResult:
        self.prepare()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT OR REPLACE INTO ai_benchmark_results
                (result_id, benchmark_run_id, case_id, task_id, domain, provider, model,
                 prompt_id, prompt_version, metrics, latency_ms, input_tokens, output_tokens,
                 total_tokens, estimated_cost, fallback_used, schema_valid, error_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.result_id,
                    result.benchmark_run_id,
                    result.case_id,
                    result.task_id,
                    result.domain,
                    result.provider,
                    result.model,
                    result.prompt_id,
                    result.prompt_version,
                    _json(result.metrics),
                    result.latency_ms,
                    result.input_tokens,
                    result.output_tokens,
                    result.total_tokens,
                    result.estimated_cost,
                    int(result.fallback_used),
                    int(result.schema_valid),
                    result.error_type,
                    result.created_at.isoformat(),
                ),
            )
        return result

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """Read benchmark metadata without creating or migrating a missing database."""
        if not self.database_path.is_file():
            return []
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """SELECT benchmark_run_id, git_sha, app_version, suite, providers, models,
                          prompt_versions, seed, dataset_version, environment, started_at,
                          finished_at, status
                   FROM ai_benchmarks ORDER BY started_at DESC LIMIT ? OFFSET ?""",
                (max(1, min(limit, 500)), max(0, offset)),
            ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            for field in ("providers", "models", "prompt_versions"):
                item[field] = json.loads(item[field])
            items.append(item)
        return items


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


__all__ = ["AiBenchmark", "AiBenchmarkResult", "AiBenchmarkStore"]
