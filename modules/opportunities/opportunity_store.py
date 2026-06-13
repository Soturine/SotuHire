"""Local deduplicated store for collected public opportunities."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from modules.scraping.dedupe import opportunity_identity
from modules.scraping.schemas import ScrapedOpportunity


class StoreSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_count: int = 0
    duplicate_count: int = 0
    updated_count: int = 0


class OpportunityStore:
    """Persist collected opportunities and update changed duplicates."""

    def __init__(self, path: str | Path = "data/sotuhire-opportunities.json") -> None:
        self.path = Path(path)

    def list(self) -> list[ScrapedOpportunity]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return [ScrapedOpportunity.model_validate(item) for item in payload]
        except (OSError, ValueError):
            return []

    def save_many(self, incoming: list[ScrapedOpportunity]) -> StoreSummary:
        current = self.list()
        indexes: dict[str, int] = {}
        for index, item in enumerate(current):
            for identity in opportunity_identity(item):
                indexes[identity] = index
        summary = StoreSummary()
        for opportunity in incoming:
            existing_index = next(
                (indexes[key] for key in opportunity_identity(opportunity) if key in indexes),
                None,
            )
            if existing_index is None:
                current.append(opportunity)
                new_index = len(current) - 1
                for identity in opportunity_identity(opportunity):
                    indexes[identity] = new_index
                summary.new_count += 1
            elif current[existing_index].content_hash != opportunity.content_hash:
                current[existing_index] = opportunity
                summary.updated_count += 1
            else:
                summary.duplicate_count += 1
        self._write(current)
        return summary

    def _write(self, opportunities: list[ScrapedOpportunity]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in opportunities],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)
