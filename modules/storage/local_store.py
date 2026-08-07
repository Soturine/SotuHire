"""Small JSON store for local analysis history."""

from __future__ import annotations

from pathlib import Path

from modules.storage.database import default_data_dir
from modules.storage.json_recovery import atomic_write_json, load_json
from modules.storage.models import StoredAnalysis


class LocalStore:
    """Persist reviewed analysis records in one local JSON file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else default_data_dir() / "sotuhire-history.json"

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
        payload = load_json(self.path, validator=_list_payload, default_factory=list)
        records = [StoredAnalysis.model_validate(item) for item in payload]
        return sorted(records, key=lambda item: item.updated_at, reverse=True)

    def _write(self, records: list[StoredAnalysis]) -> None:
        payload = [record.model_dump(mode="json") for record in records]
        atomic_write_json(self.path, payload)


def _list_payload(payload: object) -> list[object]:
    if not isinstance(payload, list):
        raise ValueError("Histórico local deve conter uma lista JSON.")
    return payload
