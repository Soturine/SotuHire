"""Read-only data health checks for SQLite and legacy local stores."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.database import connect_readonly_database, default_data_dir
from modules.storage.migrations import LATEST_SCHEMA_VERSION, MigrationRunner


class DataHealthIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    store: str = ""
    record_id: str = ""


class DataHealthReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data_dir: Path
    database_path: Path
    schema_version: int = 0
    healthy: bool = True
    counts: dict[str, int] = Field(default_factory=dict)
    issues: list[DataHealthIssue] = Field(default_factory=list)


def check_data_health(
    *, data_dir: str | Path | None = None, database_path: str | Path | None = None
) -> DataHealthReport:
    """Inspect data without mutating legacy files or the database."""
    root = Path(data_dir) if data_dir is not None else default_data_dir()
    database = Path(database_path) if database_path is not None else root / "sotuhire.db"
    report = DataHealthReport(data_dir=root, database_path=database)
    _check_legacy_files(report)
    if database.exists():
        try:
            _check_database(report)
        except (OSError, sqlite3.DatabaseError, ValueError) as exc:
            report.issues.append(
                DataHealthIssue(
                    code="database_unreadable",
                    severity="error",
                    message=f"Banco SQLite inválido ou ilegível: {type(exc).__name__}.",
                    store=str(database),
                )
            )
    else:
        report.issues.append(
            DataHealthIssue(
                code="database_missing",
                severity="info",
                message="Banco SQLite ainda não existe; execute a migração quando desejar.",
                store=str(database),
            )
        )
    report.healthy = not any(item.severity == "error" for item in report.issues)
    return report


def _check_legacy_files(report: DataHealthReport) -> None:
    candidates = [
        "profile/profiles.json",
        "memory/career-profile.json",
        "memory/career-memory.jsonl",
        "sotuhire-history.json",
        "sotuhire-opportunities.json",
        "sources/imports.json",
        "public_exams/notices.json",
        "radar/radar.json",
        "radar/schedules.json",
        "companion/captures.jsonl",
        "companion/active-context.json",
        "portfolio/project-analyses.jsonl",
    ]
    for relative in candidates:
        path = report.data_dir / relative
        if not path.exists():
            continue
        try:
            records = _read_records(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            report.issues.append(
                DataHealthIssue(
                    code="legacy_json_corrupt",
                    severity="error",
                    message=f"Arquivo legado inválido: {type(exc).__name__}.",
                    store=relative,
                )
            )
            continue
        report.counts[f"legacy:{relative}"] = len(records)
        ids = [str(item.get("id", "")) for item in records if item.get("id")]
        duplicates = [key for key, count in Counter(ids).items() if count > 1]
        for duplicate in duplicates[:20]:
            report.issues.append(
                DataHealthIssue(
                    code="duplicate_id",
                    severity="warning",
                    message="ID duplicado no store legado.",
                    store=relative,
                    record_id=duplicate,
                )
            )
        if relative.endswith("career-memory.jsonl"):
            missing_refs = sum(
                1
                for item in records
                if not item.get("source_ref")
                and not item.get("source_refs")
                and not item.get("source_id")
            )
            if missing_refs:
                report.issues.append(
                    DataHealthIssue(
                        code="memory_source_ref_missing",
                        severity="warning",
                        message=f"{missing_refs} memórias não possuem referência de origem.",
                        store=relative,
                    )
                )
        for item in records:
            for field in (
                "created_at",
                "updated_at",
                "captured_at",
                "applied_at",
                "follow_up_at",
            ):
                value = item.get(field)
                if value and not _valid_datetime(value):
                    report.issues.append(
                        DataHealthIssue(
                            code="invalid_date",
                            severity="warning",
                            message=f"Data inválida no campo {field}.",
                            store=relative,
                            record_id=str(item.get("id", "")),
                        )
                    )


def _check_database(report: DataHealthReport) -> None:
    runner = MigrationRunner(report.database_path)
    report.schema_version = runner.current_version()
    if report.schema_version != LATEST_SCHEMA_VERSION:
        report.issues.append(
            DataHealthIssue(
                code="schema_version_mismatch",
                severity="error",
                message=(
                    f"Schema atual {report.schema_version}; esperado {LATEST_SCHEMA_VERSION}."
                ),
                store=str(report.database_path),
            )
        )
        return
    for error in runner.verify():
        report.issues.append(
            DataHealthIssue(
                code="database_validation_failed",
                severity="error",
                message=error,
                store=str(report.database_path),
            )
        )
    with connect_readonly_database(report.database_path) as connection:
        tables = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        for table in tables:
            report.counts[f"sqlite:{table}"] = int(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            )
            date_columns = [
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
                if str(row[1]).endswith("_at")
            ]
            for column in date_columns:
                invalid_dates = connection.execute(
                    f"SELECT rowid, {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != ''"
                ).fetchall()
                for row in invalid_dates:
                    if not _valid_datetime(row[1]):
                        report.issues.append(
                            DataHealthIssue(
                                code="invalid_date",
                                severity="warning",
                                message=f"Data inválida no campo {column}.",
                                store=table,
                                record_id=str(row[0]),
                            )
                        )
        missing_job_snapshots = connection.execute(
            "SELECT id FROM applications WHERE job_snapshot_id IS NULL"
        ).fetchall()
        for row in missing_job_snapshots[:20]:
            report.issues.append(
                DataHealthIssue(
                    code="application_job_snapshot_missing",
                    severity="warning",
                    message="Candidatura legada sem snapshot da vaga.",
                    store="applications",
                    record_id=str(row[0]),
                )
            )
        missing_sources = connection.execute(
            "SELECT id FROM opportunities WHERE source_ref = ''"
        ).fetchall()
        for row in missing_sources[:20]:
            report.issues.append(
                DataHealthIssue(
                    code="opportunity_source_missing",
                    severity="warning",
                    message="Oportunidade sem referência de origem.",
                    store="opportunities",
                    record_id=str(row[0]),
                )
            )
        missing_opportunity_snapshots = connection.execute(
            """SELECT id FROM opportunities
            WHERE NOT EXISTS (
                SELECT 1 FROM job_snapshots WHERE opportunity_id = opportunities.id
            )"""
        ).fetchall()
        for row in missing_opportunity_snapshots[:20]:
            report.issues.append(
                DataHealthIssue(
                    code="opportunity_snapshot_missing",
                    severity="warning",
                    message="Oportunidade sem snapshot imutável.",
                    store="opportunities",
                    record_id=str(row[0]),
                )
            )
        missing_notice_snapshots = connection.execute(
            """SELECT id FROM public_exam_notices
            WHERE NOT EXISTS (
                SELECT 1 FROM public_exam_snapshots WHERE notice_id = public_exam_notices.id
            )"""
        ).fetchall()
        for row in missing_notice_snapshots[:20]:
            report.issues.append(
                DataHealthIssue(
                    code="public_exam_snapshot_missing",
                    severity="warning",
                    message="Edital sem snapshot imutável.",
                    store="public_exam_notices",
                    record_id=str(row[0]),
                )
            )
        for table in (
            "job_snapshots",
            "resume_snapshots",
            "analysis_snapshots",
            "public_exam_snapshots",
        ):
            duplicates = connection.execute(
                f"""SELECT content_hash FROM {table}
                WHERE content_hash != '' GROUP BY content_hash HAVING COUNT(*) > 1"""
            ).fetchall()
            for row in duplicates[:20]:
                report.issues.append(
                    DataHealthIssue(
                        code="duplicate_snapshot_content",
                        severity="warning",
                        message="Snapshots distintos possuem conteúdo idêntico.",
                        store=table,
                        record_id=str(row[0]),
                    )
                )
        incomplete_ai = connection.execute(
            """SELECT run_id FROM ai_runs
            WHERE provider_used = '' OR analysis_mode = ''
               OR (fallback_used = 1 AND fallback_reason = '')"""
        ).fetchall()
        for row in incomplete_ai[:20]:
            report.issues.append(
                DataHealthIssue(
                    code="ai_trace_incomplete",
                    severity="warning",
                    message="Execução de IA com metadados incompletos.",
                    store="ai_runs",
                    record_id=str(row[0]),
                )
            )


def _read_records(path: Path) -> list[dict[str, object]]:
    if path.suffix.casefold() == ".jsonl":
        return [
            _dict(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return _flatten(payload)


def _flatten(value: object) -> list[dict[str, object]]:
    if isinstance(value, list):
        return [_dict(item) for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        records: list[dict[str, object]] = []
        if "id" in value:
            records.append(_dict(value))
        for item in value.values():
            if isinstance(item, list):
                records.extend(_dict(entry) for entry in item if isinstance(entry, dict))
        return records or [_dict(value)]
    raise ValueError("JSON raiz deve ser objeto ou lista.")


def _dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Registro deve ser objeto JSON.")
    return {str(key): item for key, item in value.items()}


def _valid_datetime(value: object) -> bool:
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return True
