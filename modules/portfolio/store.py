"""Atomic local store for project analysis reports."""

from __future__ import annotations

from pathlib import Path

from modules.core.opportunity_identity import normalize_opportunity_url
from modules.portfolio.schemas import ProjectAnalysisRecord


class ProjectAnalysisStore:
    """Persist one latest analysis per normalized public project URL."""

    def __init__(self, path: str | Path = "data/portfolio/project-analyses.jsonl") -> None:
        self.path = Path(path)

    def list(self) -> list[ProjectAnalysisRecord]:
        if not self.path.exists():
            return []
        try:
            return [
                ProjectAnalysisRecord.model_validate_json(line)
                for line in self.path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, ValueError):
            return []

    def save(self, record: ProjectAnalysisRecord) -> ProjectAnalysisRecord:
        records = self.list()
        identity = normalize_opportunity_url(record.payload.url)
        for index, current in enumerate(records):
            if normalize_opportunity_url(current.payload.url) == identity:
                records[index] = record
                break
        else:
            records.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            "\n".join(item.model_dump_json() for item in records) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)
        return record
