"""SQLite source of truth for opportunity intelligence and taxonomy decisions."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from modules.opportunities.intelligence import (
    OpportunityCandidate,
    OpportunityRank,
    canonical_opportunity_url,
)
from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database
from modules.taxonomy.models import TaxonomyDatasetManifest, TaxonomyMapping


def utc_now() -> datetime:
    return datetime.now(UTC)


class OpportunityObservationRecord(BaseModel):
    """One immutable public-source observation with its canonical candidate."""

    model_config = ConfigDict(extra="forbid")

    observation_id: str
    opportunity_id: str
    candidate: OpportunityCandidate
    retrieved_at: datetime


class OpportunityRankingRecord(BaseModel):
    """Persisted, versioned local ranking result."""

    model_config = ConfigDict(extra="forbid")

    ranking_id: str
    opportunity_id: str
    profile_id: str = ""
    ranking_version: str = "local-v1"
    rank: OpportunityRank
    created_at: datetime


class CareerIntelligenceRepository:
    """Single-writer repository for the v7 career-intelligence tables."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save_candidate(self, candidate: OpportunityCandidate) -> list[OpportunityObservationRecord]:
        self._ensure()
        opportunity_id = opportunity_identity(candidate)
        records: list[OpportunityObservationRecord] = []
        with connect_database(self.database_path) as connection:
            for provenance in candidate.provenance:
                observation_id = _digest(
                    "|".join(
                        [
                            provenance.provider,
                            provenance.external_id,
                            canonical_opportunity_url(provenance.url),
                            provenance.content_hash,
                        ]
                    )
                )
                created_at = utc_now()
                connection.execute(
                    """INSERT INTO opportunity_observations
                    (observation_id, opportunity_id, provider, external_id, source_url,
                     source_version, collection_method, content_hash, payload, retrieved_at,
                     created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(provider, external_id, source_url, content_hash) DO NOTHING""",
                    (
                        observation_id,
                        opportunity_id,
                        provenance.provider,
                        provenance.external_id,
                        provenance.url,
                        provenance.source_version,
                        provenance.collection_method,
                        provenance.content_hash,
                        _json(candidate),
                        provenance.retrieved_at.isoformat(),
                        created_at.isoformat(),
                    ),
                )
                records.append(
                    OpportunityObservationRecord(
                        observation_id=observation_id,
                        opportunity_id=opportunity_id,
                        candidate=candidate,
                        retrieved_at=provenance.retrieved_at,
                    )
                )
        return records

    def list_candidates(self, *, limit: int = 200) -> list[OpportunityCandidate]:
        self._ensure()
        scan_limit = max(1, min(limit, 1_000)) * 10
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """SELECT opportunity_id, payload FROM opportunity_observations
                ORDER BY retrieved_at DESC LIMIT ?""",
                (scan_limit,),
            ).fetchall()
        candidates: list[OpportunityCandidate] = []
        seen: set[str] = set()
        for row in rows:
            opportunity_id = str(row["opportunity_id"])
            if opportunity_id in seen:
                continue
            seen.add(opportunity_id)
            candidates.append(OpportunityCandidate.model_validate_json(str(row["payload"])))
            if len(candidates) >= limit:
                break
        return candidates

    def save_rankings(
        self,
        rankings: list[OpportunityRank],
        *,
        profile_id: str = "",
        ranking_version: str = "local-v1",
    ) -> list[OpportunityRankingRecord]:
        self._ensure()
        created_at = utc_now()
        records: list[OpportunityRankingRecord] = []
        with connect_database(self.database_path) as connection:
            for rank in rankings:
                opportunity_id = opportunity_identity(rank.candidate)
                ranking_id = uuid4().hex
                connection.execute(
                    """INSERT INTO opportunity_rankings
                    (ranking_id, opportunity_id, profile_id, fit_score, confidence,
                     evidence_coverage, ranking_version, payload, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ranking_id,
                        opportunity_id,
                        profile_id,
                        rank.fit_score,
                        rank.confidence,
                        rank.evidence_coverage,
                        ranking_version,
                        _json(rank),
                        created_at.isoformat(),
                    ),
                )
                records.append(
                    OpportunityRankingRecord(
                        ranking_id=ranking_id,
                        opportunity_id=opportunity_id,
                        profile_id=profile_id,
                        ranking_version=ranking_version,
                        rank=rank,
                        created_at=created_at,
                    )
                )
        return records

    def list_rankings(
        self, *, profile_id: str = "", limit: int = 200
    ) -> list[OpportunityRankingRecord]:
        self._ensure()
        query = "SELECT * FROM opportunity_rankings"
        parameters: list[object] = []
        if profile_id:
            query += " WHERE profile_id = ?"
            parameters.append(profile_id)
        query += " ORDER BY created_at DESC, fit_score DESC LIMIT ?"
        parameters.append(max(1, min(limit, 1_000)))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            OpportunityRankingRecord(
                ranking_id=str(row["ranking_id"]),
                opportunity_id=str(row["opportunity_id"]),
                profile_id=str(row["profile_id"]),
                ranking_version=str(row["ranking_version"]),
                rank=OpportunityRank.model_validate_json(str(row["payload"])),
                created_at=datetime.fromisoformat(str(row["created_at"])),
            )
            for row in rows
        ]

    def save_dataset(self, manifest: TaxonomyDatasetManifest) -> TaxonomyDatasetManifest:
        self._ensure()
        dataset_id = _digest(f"{manifest.system}|{manifest.version}|{manifest.content_sha256}")
        created_at = utc_now().isoformat()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO taxonomy_datasets
                (dataset_id, system, version, source_url, license_name, license_url,
                 content_sha256, manifest, retrieved_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system, version, content_sha256) DO UPDATE SET
                    source_url=excluded.source_url,
                    license_name=excluded.license_name,
                    license_url=excluded.license_url,
                    manifest=excluded.manifest""",
                (
                    dataset_id,
                    manifest.system,
                    manifest.version,
                    manifest.source_url,
                    manifest.license_name,
                    manifest.license_url,
                    manifest.content_sha256,
                    _json(manifest),
                    manifest.retrieved_at.isoformat(),
                    created_at,
                ),
            )
        return manifest

    def list_datasets(self, *, limit: int = 100) -> list[TaxonomyDatasetManifest]:
        self._ensure()
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT manifest FROM taxonomy_datasets ORDER BY retrieved_at DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [TaxonomyDatasetManifest.model_validate_json(str(row["manifest"])) for row in rows]

    def save_mapping(self, mapping: TaxonomyMapping) -> TaxonomyMapping:
        self._ensure()
        now = utc_now().isoformat()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO taxonomy_mappings
                (mapping_id, source_text, target_id, target_label, taxonomy_ref, match_method,
                 confidence, review_status, payload, reviewed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mapping_id) DO UPDATE SET
                    source_text=excluded.source_text,
                    target_id=excluded.target_id,
                    target_label=excluded.target_label,
                    taxonomy_ref=excluded.taxonomy_ref,
                    match_method=excluded.match_method,
                    confidence=excluded.confidence,
                    review_status=excluded.review_status,
                    payload=excluded.payload,
                    reviewed_at=excluded.reviewed_at,
                    updated_at=excluded.updated_at""",
                (
                    mapping.mapping_id,
                    mapping.source_text,
                    mapping.target_id,
                    mapping.target_label,
                    mapping.taxonomy_ref,
                    mapping.match_method.value,
                    mapping.confidence,
                    mapping.review_status,
                    _json(mapping),
                    mapping.reviewed_at.isoformat() if mapping.reviewed_at else None,
                    now,
                    now,
                ),
            )
        return mapping

    def get_mapping(self, mapping_id: str) -> TaxonomyMapping | None:
        self._ensure()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT payload FROM taxonomy_mappings WHERE mapping_id = ?", (mapping_id,)
            ).fetchone()
        return TaxonomyMapping.model_validate_json(str(row["payload"])) if row else None

    def list_mappings(self, *, review_status: str = "", limit: int = 200) -> list[TaxonomyMapping]:
        self._ensure()
        query = "SELECT payload FROM taxonomy_mappings"
        parameters: list[object] = []
        if review_status:
            query += " WHERE review_status = ?"
            parameters.append(review_status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        parameters.append(max(1, min(limit, 1_000)))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [TaxonomyMapping.model_validate_json(str(row["payload"])) for row in rows]

    def _ensure(self) -> None:
        ensure_database(self.database_path)


def opportunity_identity(candidate: OpportunityCandidate) -> str:
    """Build a stable identity without conflating different providers' external IDs."""
    if candidate.external_id:
        return _digest(f"{candidate.source}|{candidate.external_id}")
    return _digest(canonical_opportunity_url(candidate.source_url))


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json(value: BaseModel) -> str:
    return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)


__all__ = [
    "CareerIntelligenceRepository",
    "OpportunityObservationRecord",
    "OpportunityRankingRecord",
    "opportunity_identity",
]
