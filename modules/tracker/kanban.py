"""Kanban status helpers."""

from __future__ import annotations

KANBAN_COLUMNS = [
    "found",
    "analyzed",
    "good_fit",
    "applied",
    "message_sent",
    "follow_up",
    "interview",
    "technical_test",
    "rejected",
    "offer",
    "archived",
]


def is_valid_status(status: str) -> bool:
    """Return True if a status is a known Kanban column."""
    return status in KANBAN_COLUMNS
