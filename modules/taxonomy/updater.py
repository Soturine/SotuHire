"""Explicit preview/apply/rollback workflow for official taxonomy snapshots."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from modules.storage.json_recovery import atomic_write_json
from modules.storage.safe_paths import resolve_within, safe_component
from modules.taxonomy.catalog import VersionedTaxonomyStore, taxonomy_content_sha256
from modules.taxonomy.models import TaxonomyDatasetManifest, TaxonomySystem


class TaxonomyUpdatePreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_id: str
    system: TaxonomySystem
    version: str
    checksum: str
    records_count: int
    current_version: str = ""
    freshness_days: int
    source_health: Literal["valid", "invalid"]
    requires_apply: bool = True
    warnings: list[str] = Field(default_factory=list)


class TaxonomyUpdateStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: TaxonomySystem
    active_version: str = ""
    active_checksum: str = ""
    previous_versions: list[str] = Field(default_factory=list)
    applied_at: str = ""


class TaxonomyUpdater:
    """Stage immutable data locally; never download or activate it silently."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.store = VersionedTaxonomyStore(self.root)
        self.control = self.root / ".updates"

    def preview(
        self,
        manifest: TaxonomyDatasetManifest,
        records: list[dict[str, Any]],
    ) -> TaxonomyUpdatePreview:
        checksum = taxonomy_content_sha256(records)
        if checksum != manifest.content_sha256:
            raise ValueError("O checksum calculado diverge do manifesto da taxonomia.")
        source = urlparse(manifest.source_url)
        source_health = (
            "valid"
            if source.scheme.casefold() == "https" and bool(source.hostname) and not source.username
            else "invalid"
        )
        if source_health == "invalid":
            raise ValueError("A fonte oficial da taxonomia deve ser uma URL HTTPS sem credenciais.")
        preview_id = uuid4().hex
        target = resolve_within(self.control, Path("previews") / f"{preview_id}.json")
        atomic_write_json(
            target,
            {
                "manifest": manifest.model_dump(mode="json"),
                "records": records,
                "previewed_at": datetime.now(UTC).isoformat(),
            },
            backups=1,
        )
        current = self.status(manifest.system)
        freshness = max(0, (datetime.now(UTC) - manifest.retrieved_at).days)
        warnings = []
        if freshness > 180:
            warnings.append("Snapshot com mais de 180 dias; confirme a versão na fonte oficial.")
        if current.active_checksum == checksum:
            warnings.append("O mesmo checksum já está ativo; apply será idempotente.")
        return TaxonomyUpdatePreview(
            preview_id=preview_id,
            system=manifest.system,
            version=manifest.version,
            checksum=checksum,
            records_count=len(records),
            current_version=current.active_version,
            freshness_days=freshness,
            source_health=source_health,
            warnings=warnings,
        )

    def apply(self, preview_id: str) -> TaxonomyUpdateStatus:
        identifier = safe_component(preview_id, label="preview")
        target = resolve_within(self.control, Path("previews") / f"{identifier}.json")
        payload = json.loads(target.read_text(encoding="utf-8"))
        manifest = TaxonomyDatasetManifest.model_validate(payload["manifest"])
        records = payload["records"]
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise ValueError("Preview de taxonomia inválido.")
        self.store.save(manifest, records)
        current = self.status(manifest.system)
        history = [
            item
            for item in [current.active_version, *current.previous_versions]
            if item and item != manifest.version
        ][:20]
        state = TaxonomyUpdateStatus(
            system=manifest.system,
            active_version=manifest.version,
            active_checksum=manifest.content_sha256,
            previous_versions=history,
            applied_at=datetime.now(UTC).isoformat(),
        )
        atomic_write_json(self._state_path(manifest.system), state.model_dump(mode="json"))
        target.unlink(missing_ok=True)
        return state

    def preview_manifest(self, preview_id: str) -> TaxonomyDatasetManifest:
        """Read only the staged manifest so callers can persist catalog metadata on apply."""
        identifier = safe_component(preview_id, label="preview")
        target = resolve_within(self.control, Path("previews") / f"{identifier}.json")
        payload = json.loads(target.read_text(encoding="utf-8"))
        return TaxonomyDatasetManifest.model_validate(payload["manifest"])

    def rollback(self, system: TaxonomySystem) -> TaxonomyUpdateStatus:
        current = self.status(system)
        if not current.previous_versions:
            raise ValueError("Não existe versão anterior para rollback.")
        previous = current.previous_versions[0]
        manifest_path = resolve_within(self.root, Path(system) / previous / "manifest.json")
        manifest = TaxonomyDatasetManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        state = TaxonomyUpdateStatus(
            system=system,
            active_version=previous,
            active_checksum=manifest.content_sha256,
            previous_versions=[
                current.active_version,
                *[item for item in current.previous_versions[1:] if item != current.active_version],
            ][:20],
            applied_at=datetime.now(UTC).isoformat(),
        )
        atomic_write_json(self._state_path(system), state.model_dump(mode="json"))
        return state

    def status(self, system: TaxonomySystem) -> TaxonomyUpdateStatus:
        path = self._state_path(system)
        if not path.exists():
            return TaxonomyUpdateStatus(system=system)
        return TaxonomyUpdateStatus.model_validate_json(path.read_text(encoding="utf-8"))

    def _state_path(self, system: TaxonomySystem) -> Path:
        name = safe_component(system, label="sistema")
        return resolve_within(self.control, Path("state") / f"{name}.json")


__all__ = ["TaxonomyUpdatePreview", "TaxonomyUpdateStatus", "TaxonomyUpdater"]
