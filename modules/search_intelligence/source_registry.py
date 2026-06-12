"""Registry of known job sources."""

from __future__ import annotations

from modules.search_intelligence.source_ranker import DEFAULT_SOURCES, SourceProfile


def list_sources() -> list[SourceProfile]:
    """Return known sources."""
    return list(DEFAULT_SOURCES)


def find_source(name: str) -> SourceProfile | None:
    """Find a source by case-insensitive name."""
    normalized = name.casefold()
    return next((source for source in DEFAULT_SOURCES if source.name.casefold() == normalized), None)
