"""Versioned SQLite migration contracts."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

MigrationAction = Callable[[sqlite3.Connection], None]
MigrationValidation = Callable[[sqlite3.Connection], list[str]]


@dataclass(frozen=True, slots=True)
class Migration:
    """One ordered schema migration with validation and rollback guidance."""

    version: int
    description: str
    up: MigrationAction
    validation: MigrationValidation
    rollback_strategy: str
    created_at: str
