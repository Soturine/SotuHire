"""Atomic JSONL storage for local career memory."""

from __future__ import annotations

from pathlib import Path

from modules.memory.memory_index import matches_filters, relevance_score
from modules.memory.schemas import CareerMemoryItem, CareerMemoryQuery, MemoryExport, utc_now


class MemoryStore:
    """Persist career memory locally without an external database."""

    def __init__(self, path: str | Path = "data/memory/career-memory.jsonl") -> None:
        self.path = Path(path)

    def add_memory_item(self, item: CareerMemoryItem) -> CareerMemoryItem:
        """Insert or replace an item with the same id."""
        items = self.list_memory_items()
        for index, current in enumerate(items):
            if current.id == item.id:
                items[index] = item.model_copy(update={"updated_at": utc_now()})
                break
        else:
            items.append(item)
        self._write(items)
        return next(current for current in items if current.id == item.id)

    def update_memory_item(self, item_id: str, **changes: object) -> CareerMemoryItem:
        """Update one existing memory item."""
        current = self.get_memory_item(item_id)
        if current is None:
            raise KeyError(f"Memória não encontrada: {item_id}")
        updated = current.model_copy(update={**changes, "updated_at": utc_now()})
        return self.add_memory_item(CareerMemoryItem.model_validate(updated))

    def delete_memory_item(self, item_id: str) -> bool:
        """Delete one item and return whether it existed."""
        items = self.list_memory_items()
        filtered = [item for item in items if item.id != item_id]
        if len(filtered) == len(items):
            return False
        self._write(filtered)
        return True

    def list_memory_items(self, *, kind: str = "") -> list[CareerMemoryItem]:
        """Return newest memory items, optionally filtered by kind."""
        if not self.path.exists():
            return []
        items: list[CareerMemoryItem] = []
        try:
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    items.append(CareerMemoryItem.model_validate_json(line))
        except (OSError, ValueError):
            return []
        filtered = [item for item in items if not kind or item.kind == kind]
        return sorted(filtered, key=lambda item: item.updated_at, reverse=True)

    def get_memory_item(self, item_id: str) -> CareerMemoryItem | None:
        """Return one memory item by id."""
        return next((item for item in self.list_memory_items() if item.id == item_id), None)

    def search_memory_items(
        self, query: CareerMemoryQuery | str
    ) -> list[tuple[CareerMemoryItem, float]]:
        """Search locally and return scored items."""
        request = query if isinstance(query, CareerMemoryQuery) else CareerMemoryQuery(query=query)
        scored = [
            (item, relevance_score(request.query, item))
            for item in self.list_memory_items()
            if matches_filters(item, request.filters)
        ]
        return [
            (item, score)
            for item, score in sorted(scored, key=lambda pair: pair[1], reverse=True)
            if score > 0
        ][: request.top_k]

    def clear(self) -> None:
        """Delete all local memory items."""
        if self.path.exists():
            self.path.unlink()

    def export_json(self, path: str | Path) -> Path:
        """Export a portable JSON memory bundle."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = MemoryExport(items=self.list_memory_items()).model_dump_json(indent=2)
        target.write_text(payload, encoding="utf-8")
        return target

    def export_jsonl(self, path: str | Path) -> Path:
        """Export memory as JSONL."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "\n".join(item.model_dump_json() for item in self.list_memory_items()) + "\n",
            encoding="utf-8",
        )
        return target

    def import_file(self, path: str | Path) -> int:
        """Import JSON or JSONL memory and return inserted item count."""
        source = Path(path)
        text = source.read_text(encoding="utf-8")
        if source.suffix.lower() == ".jsonl":
            items = [
                CareerMemoryItem.model_validate_json(line)
                for line in text.splitlines()
                if line.strip()
            ]
        else:
            items = MemoryExport.model_validate_json(text).items
        for item in items:
            self.add_memory_item(item)
        return len(items)

    def _write(self, items: list[CareerMemoryItem]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            "\n".join(item.model_dump_json() for item in items) + ("\n" if items else ""),
            encoding="utf-8",
        )
        temporary.replace(self.path)
