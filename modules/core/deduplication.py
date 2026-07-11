"""Small deterministic deduplication primitives that preserve original records."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

ItemT = TypeVar("ItemT")


def duplicate_groups(items: Iterable[ItemT], identity: Callable[[ItemT], str]) -> list[list[ItemT]]:
    """Return only duplicate groups; callers decide whether and how to merge."""
    grouped: dict[str, list[ItemT]] = {}
    for item in items:
        key = identity(item)
        if key:
            grouped.setdefault(key, []).append(item)
    return [group for group in grouped.values() if len(group) > 1]


def unique_preserving_order(
    items: Iterable[ItemT], identity: Callable[[ItemT], str]
) -> list[ItemT]:
    """Keep the first record for each identity without mutating or deleting inputs."""
    result: list[ItemT] = []
    seen: set[str] = set()
    for item in items:
        key = identity(item)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        result.append(item)
    return result
