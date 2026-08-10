"""Content-addressed local cache for official taxonomy snapshots."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from modules.storage.json_recovery import atomic_write_json
from modules.storage.safe_paths import resolve_within, safe_component
from modules.taxonomy.models import TaxonomyDatasetManifest


class VersionedTaxonomyStore:
    """Persist immutable verified snapshots without downloading data implicitly."""

    def __init__(self, root: str | Path = "data/taxonomies") -> None:
        self.root = Path(root).resolve()

    def save(
        self,
        manifest: TaxonomyDatasetManifest,
        records: list[dict[str, Any]],
    ) -> Path:
        encoded = _encoded(records)
        digest = hashlib.sha256(encoded).hexdigest()
        if digest != manifest.content_sha256:
            raise ValueError("O hash do dataset de taxonomia nao corresponde ao manifesto.")
        target = self._path(manifest)
        if target.exists() and target.read_bytes() != encoded:
            raise ValueError("Snapshot de taxonomia imutavel divergiu do cache local.")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(encoded)
            temporary.replace(target)
        atomic_write_json(target.parent / "manifest.json", manifest.model_dump(mode="json"))
        return target

    def load(self, manifest: TaxonomyDatasetManifest) -> list[dict[str, Any]]:
        target = self._path(manifest)
        payload = target.read_bytes()
        if hashlib.sha256(payload).hexdigest() != manifest.content_sha256:
            raise ValueError("O cache local de taxonomia falhou na verificacao de integridade.")
        decoded = json.loads(payload.decode("utf-8"))
        if not isinstance(decoded, list) or not all(isinstance(item, dict) for item in decoded):
            raise ValueError("O dataset de taxonomia possui um contrato invalido.")
        return decoded

    def _path(self, manifest: TaxonomyDatasetManifest) -> Path:
        system = safe_component(manifest.system, label="sistema")
        version = safe_component(manifest.version, label="versao")
        checksum = safe_component(manifest.content_sha256, label="checksum")
        return resolve_within(self.root, Path(system) / version / f"{checksum}.json")


def taxonomy_content_sha256(records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_encoded(records)).hexdigest()


def _encoded(records: list[dict[str, Any]]) -> bytes:
    return json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


__all__ = ["VersionedTaxonomyStore", "taxonomy_content_sha256"]
