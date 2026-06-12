"""Small JSON store for local analysis history."""

from __future__ import annotations

import json
from pathlib import Path

from modules.storage.models import StoredAnalysis


class LocalStore:
    """Persist reviewed analysis records in one local JSON file."""

    def __init__(self, path: str | Path = "data/sotuhire-history.json") -> None:
        self.path = Path(path)

    def save(self, record: StoredAnalysis) -> StoredAnalysis:
        """Insert or replace a record after explicit privacy acknowledgement."""
        if not record.privacy_acknowledged:
            raise ValueError("Confirme o aviso de privacidade antes de salvar.")

        records = self.list_analyses()
        for index, current in enumerate(records):
            if current.id == record.id:
                records[index] = record
                break
        else:
            records.append(record)
        self._write(records)
        return record

    def get(self, record_id: str) -> StoredAnalysis | None:
        """Return one stored analysis by id."""
        return next((record for record in self.list_analyses() if record.id == record_id), None)

    def list_analyses(self) -> list[StoredAnalysis]:
        """Return records from newest to oldest."""
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        records = [StoredAnalysis.model_validate(item) for item in payload]
        return sorted(records, key=lambda item: item.updated_at, reverse=True)

    def _write(self, records: list[StoredAnalysis]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        payload = [record.model_dump(mode="json") for record in records]
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)
