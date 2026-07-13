"""Safe, idempotent migration from SotuHire JSON/JSONL stores to SQLite."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from modules.core.entity_identity import (
    content_fingerprint,
    normalize_entity_url,
    profile_item_identity,
    project_identity,
)
from modules.storage.backup import create_backup
from modules.storage.database import connect_database, default_data_dir
from modules.storage.migrations import MigrationRunner

LEGACY_PATHS = (
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
)


class LegacyMigrationReport(BaseModel):
    """Machine-readable migration summary without record contents."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["dry-run", "apply", "verify"]
    data_dir: Path
    database_path: Path
    found: dict[str, int] = Field(default_factory=dict)
    imported: dict[str, int] = Field(default_factory=dict)
    duplicates: dict[str, int] = Field(default_factory=dict)
    rejected: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    backup_path: Path | None = None
    schema_version: int = 0
    original_files_preserved: bool = True
    success: bool = False


@dataclass(frozen=True, slots=True)
class LegacyEntity:
    table: str
    entity_id: str
    payload: dict[str, Any]
    source_path: str
    source_checksum: str
    source_ref: str = ""
    parent_id: str = ""

    @property
    def content_hash(self) -> str:
        return _payload_hash(self.payload)


def migrate_local_data(
    *,
    mode: Literal["dry-run", "apply", "verify"] = "dry-run",
    data_dir: str | Path | None = None,
    database_path: str | Path | None = None,
) -> LegacyMigrationReport:
    """Inspect, apply or verify migration without deleting legacy stores."""
    root = Path(data_dir) if data_dir is not None else default_data_dir()
    database = Path(database_path) if database_path is not None else root / "sotuhire.db"
    report = LegacyMigrationReport(mode=mode, data_dir=root, database_path=database)
    if mode == "verify":
        runner = MigrationRunner(database)
        report.schema_version = runner.current_version()
        report.warnings.extend(runner.verify())
        report.success = not report.warnings
        return report

    entities = _discover(root, report)
    report.found = _counts(entities)
    entities, duplicates = _deduplicate_entities(entities)
    report.duplicates.update(duplicates)
    if mode == "dry-run":
        report.success = not any(report.rejected.values())
        return report

    report.backup_path = create_backup(data_dir=root).archive_path
    runner = MigrationRunner(database)
    runner.apply(create_backup=True)
    report.schema_version = runner.current_version()
    imported: dict[str, int] = {}
    skipped: dict[str, int] = {}
    with connect_database(database) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            for entity in entities:
                already_imported = connection.execute(
                    """SELECT 1 FROM legacy_migration_history
                    WHERE source_path = ? AND source_checksum = ?
                      AND entity_type = ? AND entity_id = ?""",
                    (
                        entity.source_path,
                        entity.source_checksum,
                        entity.table,
                        entity.entity_id,
                    ),
                ).fetchone()
                if already_imported is not None:
                    skipped[entity.table] = skipped.get(entity.table, 0) + 1
                    continue
                _insert_entity(connection, entity, report)
                connection.execute(
                    """INSERT INTO legacy_migration_history
                    (source_path, source_checksum, entity_type, entity_id, migrated_at, payload_hash)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        entity.source_path,
                        entity.source_checksum,
                        entity.table,
                        entity.entity_id,
                        datetime.now(UTC).isoformat(),
                        entity.content_hash,
                    ),
                )
                imported[entity.table] = imported.get(entity.table, 0) + 1
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    report.imported = imported
    for table, count in skipped.items():
        report.duplicates[table] = report.duplicates.get(table, 0) + count
    verification_errors = runner.verify()
    report.warnings.extend(verification_errors)
    report.success = not verification_errors and not any(report.rejected.values())
    return report


def _discover(root: Path, report: LegacyMigrationReport) -> list[LegacyEntity]:
    entities: list[LegacyEntity] = []
    for relative in LEGACY_PATHS:
        path = root / relative
        if not path.exists():
            continue
        checksum = _file_hash(path)
        payloads = _load_file(path, relative, report)
        for payload in payloads:
            entities.extend(_map_payload(relative, checksum, payload, report))
    return entities


def _load_file(path: Path, relative: str, report: LegacyMigrationReport) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".jsonl":
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("registro não é objeto")
                records.append(value)
            except (ValueError, json.JSONDecodeError) as exc:
                _reject(report, relative, f"linha {line_number} inválida ({type(exc).__name__})")
        return records
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _reject(report, relative, f"arquivo inválido ({type(exc).__name__})")
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    _reject(report, relative, "raiz JSON deve ser objeto ou lista")
    return []


def _map_payload(
    relative: str,
    checksum: str,
    payload: dict[str, Any],
    report: LegacyMigrationReport,
) -> list[LegacyEntity]:
    make = lambda table, entity_id, item, source_ref="", parent_id="": LegacyEntity(  # noqa: E731
        table, entity_id, item, relative, checksum, source_ref, parent_id
    )
    entities: list[LegacyEntity] = []
    if relative == "profile/profiles.json":
        for profile in _list(payload.get("profiles")):
            profile_id = _id(profile, "profile_id", fallback=_stable_id("profile", profile))
            entities.append(make("profiles", profile_id, profile))
            for item in _list(profile.get("items")) + _list(profile.get("constraints")):
                item_id = _id(item, "item_id", fallback=_stable_id("profile-item", item))
                entities.append(
                    make(
                        "profile_items",
                        item_id,
                        item,
                        str(item.get("source_ref", "")),
                        profile_id,
                    )
                )
    elif relative == "memory/career-profile.json":
        entities.append(make("profiles", "legacy-career-profile", payload, parent_id="legacy"))
    elif relative == "memory/career-memory.jsonl":
        entity_id = _id(payload, "id", fallback=_stable_id("memory", payload))
        source_ref = _first_text(payload.get("source_refs")) or str(payload.get("source_id", ""))
        entities.append(make("memories", entity_id, payload, source_ref))
    elif relative == "sotuhire-history.json":
        entity_id = _id(payload, "id", fallback=_stable_id("application", payload))
        entities.append(
            make("applications", entity_id, payload, str(payload.get("source_url", "")))
        )
        if not payload.get("job_snapshot_id"):
            report.warnings.append(
                f"{relative}: candidatura {entity_id} sem texto original; snapshot não inventado."
            )
    elif relative == "sotuhire-opportunities.json":
        entity_id = _id(payload, "id", fallback=_stable_id("opportunity", payload))
        source_ref = str(payload.get("source_url", ""))
        entities.append(make("opportunities", entity_id, payload, source_ref))
        if str(payload.get("description", "")).strip():
            entities.append(
                make(
                    "job_snapshots",
                    _stable_id("job-snapshot", payload),
                    payload,
                    source_ref,
                    entity_id,
                )
            )
    elif relative == "sources/imports.json":
        for item in _list(payload.get("sources")):
            entities.append(
                make(
                    "sources",
                    _id(item, "id", fallback=_stable_id("source", item)),
                    item,
                    str(item.get("source_url", "")),
                )
            )
        for item in _list(payload.get("captures")):
            capture_id = _id(item, "id", fallback=_stable_id("capture", item))
            source_ref = str(item.get("source_url") or item.get("job_url") or "")
            entities.append(make("captures", capture_id, item, source_ref))
            if str(item.get("raw_text", "")).strip():
                entities.append(
                    make(
                        "job_snapshots",
                        _stable_id("job-snapshot", item),
                        item,
                        source_ref,
                        capture_id,
                    )
                )
    elif relative == "public_exams/notices.json":
        for notice in _list(payload.get("notices")):
            notice_id = _id(notice, "notice_id", fallback=_stable_id("notice", notice))
            source_ref = str(notice.get("source_url", ""))
            entities.append(make("public_exam_notices", notice_id, notice, source_ref))
            for role in _list(notice.get("roles")):
                role_id = _id(role, "role_id", fallback=_stable_id("exam-role", role))
                entities.append(make("public_exam_roles", role_id, role, source_ref, notice_id))
                for requirement in _list(role.get("requirements")):
                    requirement_id = _id(
                        requirement,
                        "requirement_id",
                        fallback=_stable_id("exam-requirement", requirement),
                    )
                    entities.append(
                        make(
                            "public_exam_requirements",
                            requirement_id,
                            requirement,
                            source_ref,
                            role_id,
                        )
                    )
            if str(notice.get("raw_text", "")).strip():
                entities.append(
                    make(
                        "public_exam_snapshots",
                        _stable_id("public-exam-snapshot", notice),
                        notice,
                        source_ref,
                        notice_id,
                    )
                )
    elif relative == "radar/radar.json":
        mapping = {
            "wishlists": "radar_wishlists",
            "sources": "radar_sources",
            "runs": "radar_runs",
            "results": "radar_results",
            "alerts": "notifications",
        }
        for key, table in mapping.items():
            for item in _list(payload.get(key)):
                entity_id = _id(item, "id", fallback=_stable_id(table, item))
                source_ref = str(item.get("url") or item.get("result_id") or "")
                parent_id = str(item.get("run_id", ""))
                entities.append(make(table, entity_id, item, source_ref, parent_id))
    elif relative == "radar/schedules.json":
        mapping = {
            "schedules": ("schedules", "schedule_id"),
            "scheduled_runs": ("radar_runs", "run_id"),
            "notifications": ("notifications", "notification_id"),
        }
        for key, (table, id_field) in mapping.items():
            for item in _list(payload.get(key)):
                entities.append(
                    make(table, _id(item, id_field, fallback=_stable_id(table, item)), item)
                )
    elif relative == "companion/captures.jsonl":
        capture_id = _id(payload, "id", fallback=_stable_id("capture", payload))
        nested_capture = payload.get("capture")
        capture: dict[str, Any] = nested_capture if isinstance(nested_capture, dict) else payload
        source_ref = str(capture.get("url", ""))
        entities.append(make("captures", capture_id, payload, source_ref))
        text = str(capture.get("description") or capture.get("visible_text") or "").strip()
        if str(capture.get("kind", "job")) == "job" and text:
            job_payload = {**capture, "raw_text": text}
            entities.append(
                make(
                    "job_snapshots",
                    _stable_id("job-snapshot", job_payload),
                    job_payload,
                    source_ref,
                    capture_id,
                )
            )
    elif relative == "companion/active-context.json":
        if str(payload.get("resume_text", "")).strip():
            entities.append(
                make(
                    "resume_snapshots",
                    _stable_id("resume-snapshot", payload),
                    payload,
                    parent_id="legacy-active-context",
                )
            )
    elif relative == "portfolio/project-analyses.jsonl":
        nested_report = payload.get("report")
        report_payload: dict[str, Any] = (
            nested_report if isinstance(nested_report, dict) else payload
        )
        entity_id = _id(report_payload, "id", fallback=_stable_id("github-project", payload))
        source_ref = str(report_payload.get("url") or "")
        entities.append(make("github_projects", entity_id, payload, source_ref))
    return entities


def _insert_entity(connection: Any, entity: LegacyEntity, report: LegacyMigrationReport) -> None:
    if entity.table == "applications":
        _insert_application(connection, entity)
    elif entity.table == "job_snapshots":
        _insert_job_snapshot(connection, entity)
    elif entity.table == "resume_snapshots":
        _insert_resume_snapshot(connection, entity)
    elif entity.table == "public_exam_snapshots":
        _insert_public_exam_snapshot(connection, entity)
    elif entity.table == "profile_items":
        _insert_profile_item(connection, entity)
    elif entity.table == "public_exam_roles":
        _insert_child(connection, entity, "notice_id")
    elif entity.table == "public_exam_requirements":
        _insert_child(connection, entity, "role_id")
    elif entity.table == "radar_results":
        _insert_radar_result(connection, entity)
    else:
        _insert_generic(connection, entity)


def _insert_generic(connection: Any, entity: LegacyEntity) -> None:
    now = _timestamp(entity.payload)
    connection.execute(
        f"""INSERT INTO {entity.table}
        (id, payload, source_ref, content_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            payload=excluded.payload,
            source_ref=CASE WHEN excluded.source_ref != '' THEN excluded.source_ref ELSE source_ref END,
            content_hash=excluded.content_hash,
            updated_at=excluded.updated_at""",
        (
            entity.entity_id,
            _json(entity.payload),
            entity.source_ref,
            entity.content_hash,
            now,
            now,
        ),
    )


def _insert_profile_item(connection: Any, entity: LegacyEntity) -> None:
    now = _timestamp(entity.payload)
    connection.execute(
        """INSERT INTO profile_items
        (id, profile_id, payload, source_ref, content_hash, confirmed_by_user,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, source_ref=excluded.source_ref,
        content_hash=excluded.content_hash, confirmed_by_user=excluded.confirmed_by_user,
        updated_at=excluded.updated_at""",
        (
            entity.entity_id,
            entity.parent_id,
            _json(entity.payload),
            entity.source_ref,
            entity.content_hash,
            int(bool(entity.payload.get("confirmed_by_user"))),
            now,
            now,
        ),
    )


def _insert_child(connection: Any, entity: LegacyEntity, parent_field: str) -> None:
    now = _timestamp(entity.payload)
    connection.execute(
        f"""INSERT INTO {entity.table}
        (id, {parent_field}, payload, source_ref, content_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,
        source_ref=excluded.source_ref, content_hash=excluded.content_hash,
        updated_at=excluded.updated_at""",
        (
            entity.entity_id,
            entity.parent_id,
            _json(entity.payload),
            entity.source_ref,
            entity.content_hash,
            now,
            now,
        ),
    )


def _insert_radar_result(connection: Any, entity: LegacyEntity) -> None:
    now = _timestamp(entity.payload)
    run_id = entity.parent_id
    if run_id:
        exists = connection.execute("SELECT 1 FROM radar_runs WHERE id = ?", (run_id,)).fetchone()
        if exists is None:
            run_id = ""
    connection.execute(
        """INSERT INTO radar_results
        (id, run_id, payload, source_ref, content_hash, created_at, updated_at)
        VALUES (?, NULLIF(?, ''), ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, source_ref=excluded.source_ref,
        content_hash=excluded.content_hash, updated_at=excluded.updated_at""",
        (
            entity.entity_id,
            run_id,
            _json(entity.payload),
            entity.source_ref,
            entity.content_hash,
            now,
            now,
        ),
    )


def _insert_application(connection: Any, entity: LegacyEntity) -> None:
    payload = entity.payload
    now = _timestamp(payload)
    status = str(payload.get("status", "found"))
    if status.startswith("JobStatus."):
        status = status.split(".")[-1].casefold()
    connection.execute(
        """INSERT INTO applications
        (id, job_title, organization, source_url, status, applied_at, stage_history,
         contact_history, interview_notes, outcome, outcome_reason, payload, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, status=excluded.status,
        updated_at=excluded.updated_at""",
        (
            entity.entity_id,
            str(payload.get("job_title", "")),
            str(payload.get("company", "")),
            str(payload.get("source_url", "")),
            status,
            payload.get("applied_at"),
            _json(payload.get("stage_history", [])),
            _json(payload.get("contact_history", [])),
            str(payload.get("interview_notes", "")),
            str(payload.get("outcome", "")),
            str(payload.get("outcome_reason", "")),
            _json(payload),
            str(payload.get("created_at", now)),
            str(payload.get("updated_at", now)),
        ),
    )


def _insert_job_snapshot(connection: Any, entity: LegacyEntity) -> None:
    payload = entity.payload
    now = _timestamp(payload)
    opportunity_id = entity.parent_id
    if opportunity_id:
        connection.execute(
            """INSERT OR IGNORE INTO opportunities
            (id, payload, source_ref, content_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                opportunity_id,
                _json({"id": opportunity_id, "source_url": entity.source_ref}),
                entity.source_ref,
                entity.content_hash,
                now,
                now,
            ),
        )
    raw_text = str(
        payload.get("raw_text") or payload.get("description") or payload.get("visible_text") or ""
    )
    connection.execute(
        """INSERT OR IGNORE INTO job_snapshots
        (snapshot_id, opportunity_id, title, organization, location, description,
         source_url, source_refs, captured_at, content_hash, source_kind, raw_text,
         structured_data)
        VALUES (?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            entity.entity_id,
            opportunity_id,
            str(
                payload.get("title") or payload.get("job_title") or payload.get("page_title") or ""
            ),
            str(payload.get("company") or payload.get("organization") or ""),
            str(payload.get("location", "")),
            raw_text,
            entity.source_ref,
            _json([entity.source_ref] if entity.source_ref else []),
            str(payload.get("captured_at") or payload.get("collected_at") or now),
            entity.content_hash,
            str(payload.get("origin") or payload.get("collection_method") or "legacy"),
            raw_text,
            _json(payload),
        ),
    )


def _insert_resume_snapshot(connection: Any, entity: LegacyEntity) -> None:
    payload = entity.payload
    content = str(payload.get("resume_text", ""))
    now = _timestamp(payload)
    connection.execute(
        """INSERT OR IGNORE INTO resume_snapshots
        (snapshot_id, resume_variant_id, title, content, structured_sections,
         source_profile_item_ids, created_at, content_hash)
        VALUES (?, 'legacy-active-context', 'Currículo do contexto legado', ?, '{}', '[]', ?, ?)""",
        (entity.entity_id, content, now, entity.content_hash),
    )


def _insert_public_exam_snapshot(connection: Any, entity: LegacyEntity) -> None:
    payload = entity.payload
    now = _timestamp(payload)
    connection.execute(
        """INSERT OR IGNORE INTO public_exam_snapshots
        (snapshot_id, notice_id, raw_text, structured_notice, requirements,
         timeline, content_hash, captured_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            entity.entity_id,
            entity.parent_id,
            str(payload.get("raw_text", "")),
            _json(payload),
            _json(payload.get("general_requirements", [])),
            _json(_timeline_entries(payload.get("timeline"))),
            entity.content_hash,
            str(payload.get("created_at", now)),
        ),
    )


def _counts(entities: list[LegacyEntity]) -> dict[str, int]:
    result: dict[str, int] = {}
    for entity in entities:
        result[entity.table] = result.get(entity.table, 0) + 1
    return result


def _timeline_entries(value: object) -> list[dict[str, Any] | str]:
    if isinstance(value, dict):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, (dict, str))]
    return []


def _deduplicate_entities(
    entities: list[LegacyEntity],
) -> tuple[list[LegacyEntity], dict[str, int]]:
    """Merge only strong or exact identities and retain all legacy provenance."""
    by_identity: dict[tuple[str, str], LegacyEntity] = {}
    order: list[tuple[str, str]] = []
    duplicates: dict[str, int] = {}
    for entity in entities:
        identity = (entity.table, _semantic_identity(entity))
        existing = by_identity.get(identity)
        if existing is None:
            by_identity[identity] = entity
            order.append(identity)
            continue
        by_identity[identity] = _merge_legacy_entities(existing, entity)
        duplicates[entity.table] = duplicates.get(entity.table, 0) + 1
    return [by_identity[key] for key in order], duplicates


def _semantic_identity(entity: LegacyEntity) -> str:
    payload = entity.payload
    if entity.table == "memories" and str(payload.get("kind", "")) not in {
        "tracker_event",
        "feedback",
    }:
        exact = content_fingerprint(
            str(payload.get("kind", "")),
            str(payload.get("title", "")),
            str(payload.get("content", "")),
        )
        if exact:
            return f"memory-content:{exact}"
    if entity.table in {"opportunities", "captures"}:
        nested = payload.get("capture")
        item = nested if isinstance(nested, dict) else payload
        url = normalize_entity_url(
            str(item.get("source_url") or item.get("job_url") or item.get("url") or "")
        )
        if url:
            return f"url:{url}"
    if entity.table == "profile_items":
        return profile_item_identity(
            item_type=str(payload.get("type", "other")),
            title=str(payload.get("title", "")),
            source=str(payload.get("source", "")),
            source_ref=str(payload.get("source_ref", "")),
            evidence=str(payload.get("evidence") or payload.get("description") or ""),
        )
    if entity.table == "github_projects":
        nested = payload.get("report")
        item = nested if isinstance(nested, dict) else payload
        identity = project_identity(
            url=str(item.get("url", "")),
            owner=str(item.get("owner", "")),
            repo=str(item.get("repo", "")),
            title=str(item.get("title", "")),
        )
        if not identity.endswith(":"):
            return identity
    if entity.table == "job_snapshots":
        raw_text = str(
            payload.get("raw_text")
            or payload.get("description")
            or payload.get("visible_text")
            or ""
        )
        exact = content_fingerprint(
            normalize_entity_url(entity.source_ref),
            str(payload.get("title") or payload.get("job_title") or ""),
            str(payload.get("company") or payload.get("organization") or ""),
            raw_text,
        )
        if exact:
            return f"job-snapshot:{exact}"
    if entity.table == "resume_snapshots":
        exact = content_fingerprint(str(payload.get("resume_text", "")))
        if exact:
            return f"resume-snapshot:{exact}"
    if entity.table == "public_exam_snapshots":
        exact = content_fingerprint(entity.parent_id, str(payload.get("raw_text", "")))
        if exact:
            return f"public-exam-snapshot:{exact}"
    return f"id:{entity.entity_id}"


def _merge_legacy_entities(left: LegacyEntity, right: LegacyEntity) -> LegacyEntity:
    payload = _merge_payload(left.payload, right.payload)
    source_paths = list(
        dict.fromkeys(
            [
                *[str(item) for item in payload.get("legacy_source_paths", [])],
                *left.source_path.split("|"),
                *right.source_path.split("|"),
            ]
        )
    )
    merged_ids = [
        *[str(item) for item in payload.get("merged_legacy_ids", []) if str(item).strip()],
        left.entity_id,
        right.entity_id,
    ]
    payload["merged_legacy_ids"] = list(dict.fromkeys(merged_ids))
    payload["deduplication_reason"] = "strong_or_exact_identity_during_legacy_migration"
    source_refs = [
        *[str(item) for item in payload.get("source_refs", []) if str(item).strip()],
        left.source_ref,
        right.source_ref,
    ]
    payload["source_refs"] = list(dict.fromkeys(item for item in source_refs if item))
    payload["legacy_source_paths"] = source_paths
    composite_checksum = hashlib.sha256(
        "|".join(
            sorted(
                [
                    left.source_checksum,
                    right.source_checksum,
                ]
            )
        ).encode("utf-8")
    ).hexdigest()
    return LegacyEntity(
        table=left.table,
        entity_id=left.entity_id,
        payload=payload,
        source_path="|".join(source_paths),
        source_checksum=composite_checksum,
        source_ref=left.source_ref or right.source_ref,
        parent_id=left.parent_id or right.parent_id,
    )


def _merge_payload(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = dict(left)
    for key, value in right.items():
        current = merged.get(key)
        if current in (None, "", [], {}):
            merged[key] = value
        elif isinstance(current, list) and isinstance(value, list):
            merged[key] = list({_json(item): item for item in [*current, *value]}.values())
    return merged


def _reject(report: LegacyMigrationReport, store: str, reason: str) -> None:
    report.rejected[store] = report.rejected.get(store, 0) + 1
    report.warnings.append(f"{store}: {reason}; origem preservada e item não importado.")


def _id(payload: dict[str, Any], field: str, *, fallback: str) -> str:
    return str(payload.get(field) or fallback)


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _first_text(value: object) -> str:
    if not isinstance(value, list):
        return ""
    return next((str(item) for item in value if str(item).strip()), "")


def _stable_id(prefix: str, payload: object) -> str:
    return f"{prefix}-{_payload_hash(payload)[:24]}"


def _payload_hash(payload: object) -> str:
    content = _json(payload)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(payload: object) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def _timestamp(payload: dict[str, Any]) -> str:
    return str(
        payload.get("updated_at")
        or payload.get("created_at")
        or payload.get("captured_at")
        or datetime.now(UTC).isoformat()
    )
