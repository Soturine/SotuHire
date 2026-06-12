"""Kanban status helpers."""

from __future__ import annotations

from modules.tracker.status import JobStatus

KANBAN_COLUMNS = [status.value for status in JobStatus]


def is_valid_status(status: str) -> bool:
    """Return True if a status is a known Kanban column."""
    return status in KANBAN_COLUMNS
