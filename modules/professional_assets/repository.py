"""SQLite repository for reusable professional assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.evidence import EvidenceReviewStatus
from modules.professional_assets.models import AssetStatus, ProfessionalAsset, utc_now
from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database


class ProfessionalAssetRepository:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save(self, asset: ProfessionalAsset) -> ProfessionalAsset:
        validated = ProfessionalAsset.model_validate(asset.model_dump())
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            if validated.profile_id:
                now = validated.updated_at.isoformat()
                connection.execute(
                    """INSERT OR IGNORE INTO profiles
                    (id, payload, source_ref, content_hash, created_at, updated_at)
                    VALUES (?, ?, '', '', ?, ?)""",
                    (validated.profile_id, _json({"id": validated.profile_id}), now, now),
                )
            connection.execute(
                """INSERT INTO professional_assets
                (asset_id, profile_id, session_id, target_opportunity_id, asset_type, title,
                 content, structured_content, evidence_scope_id, evidence_scope, source_refs,
                 evidence_ids, document_snapshot_ids, dependency_hash, status, review_status,
                 stale_at, stale_reason, created_at, updated_at)
                VALUES (?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    title=excluded.title,
                    content=excluded.content,
                    structured_content=excluded.structured_content,
                    evidence_scope_id=excluded.evidence_scope_id,
                    evidence_scope=excluded.evidence_scope,
                    source_refs=excluded.source_refs,
                    evidence_ids=excluded.evidence_ids,
                    document_snapshot_ids=excluded.document_snapshot_ids,
                    dependency_hash=excluded.dependency_hash,
                    status=excluded.status,
                    review_status=excluded.review_status,
                    stale_at=excluded.stale_at,
                    stale_reason=excluded.stale_reason,
                    updated_at=excluded.updated_at""",
                (
                    validated.asset_id,
                    validated.profile_id,
                    validated.application_lab_session_id,
                    validated.target_opportunity_id,
                    validated.asset_type,
                    validated.title,
                    validated.content,
                    _json(validated.structured_content),
                    validated.evidence_scope_id,
                    _json(validated.evidence_scope),
                    _json(validated.source_refs),
                    _json(validated.evidence_ids),
                    _json(validated.document_snapshot_ids),
                    validated.dependency_hash,
                    validated.status,
                    validated.review_status,
                    validated.stale_at.isoformat() if validated.stale_at else None,
                    validated.stale_reason,
                    validated.created_at.isoformat(),
                    validated.updated_at.isoformat(),
                ),
            )
        return validated

    def get(self, asset_id: str) -> ProfessionalAsset | None:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM professional_assets WHERE asset_id = ?", (asset_id,)
            ).fetchone()
        return _from_row(row) if row is not None else None

    def list(
        self,
        *,
        asset_type: str = "",
        session_id: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ProfessionalAsset]:
        ensure_database(self.database_path)
        clauses: list[str] = []
        values: list[object] = []
        if asset_type:
            clauses.append("asset_type = ?")
            values.append(asset_type)
        if session_id:
            clauses.append("session_id = ?")
            values.append(session_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        values.extend([max(1, min(limit, 200)), max(0, offset)])
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""SELECT * FROM professional_assets {where}
                ORDER BY updated_at DESC LIMIT ? OFFSET ?""",  # noqa: S608
                values,
            ).fetchall()
        return [_from_row(row) for row in rows]

    def change_status(
        self,
        asset_id: str,
        status: AssetStatus,
        *,
        content: str | None = None,
    ) -> ProfessionalAsset | None:
        current = self.get(asset_id)
        if current is None:
            return None
        if status is AssetStatus.CONFIRMED:
            review_status = EvidenceReviewStatus.CONFIRMED
        elif status is AssetStatus.STALE:
            review_status = EvidenceReviewStatus.STALE
        elif status in {AssetStatus.DRAFT, AssetStatus.REVIEW}:
            review_status = (
                EvidenceReviewStatus.SOURCED
                if current.source_refs or current.evidence_ids
                else EvidenceReviewStatus.CANDIDATE
            )
        else:
            review_status = current.review_status
        updated = current.model_copy(
            update={
                "status": status,
                "content": current.content if content is None else content,
                "review_status": review_status,
                "updated_at": utc_now(),
                "stale_at": utc_now() if status is AssetStatus.STALE else None,
                "stale_reason": (current.stale_reason if status is AssetStatus.STALE else ""),
            }
        )
        return self.save(ProfessionalAsset.model_validate(updated.model_dump()))

    def mark_session_stale(self, session_id: str, reason: str) -> int:
        if not session_id:
            return 0
        ensure_database(self.database_path)
        now = utc_now().isoformat()
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """UPDATE professional_assets
                SET status='stale', review_status='stale', stale_at=?, stale_reason=?, updated_at=?
                WHERE session_id=? AND status NOT IN ('archived', 'stale')""",
                (now, reason.strip() or "upstream_dependency_changed", now, session_id),
            )
        return cursor.rowcount


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _load(value: object, default: Any) -> Any:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError):
        return default


def _from_row(row: Any) -> ProfessionalAsset:
    return ProfessionalAsset(
        asset_id=row["asset_id"],
        asset_type=row["asset_type"],
        title=row["title"],
        status=row["status"],
        content=row["content"],
        structured_content=_load(row["structured_content"], {}),
        profile_id=row["profile_id"] or "",
        target_opportunity_id=row["target_opportunity_id"] or "",
        application_lab_session_id=row["session_id"] or "",
        evidence_scope_id=row["evidence_scope_id"],
        evidence_scope=_load(row["evidence_scope"], {}),
        source_refs=_load(row["source_refs"], []),
        evidence_ids=_load(row["evidence_ids"], []),
        document_snapshot_ids=_load(row["document_snapshot_ids"], []),
        dependency_hash=row["dependency_hash"],
        review_status=row["review_status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        stale_at=row["stale_at"],
        stale_reason=row["stale_reason"],
    )


__all__ = ["ProfessionalAssetRepository"]
