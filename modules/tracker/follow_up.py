"""Follow-up date helpers."""

from __future__ import annotations

from datetime import date, timedelta


def next_follow_up(start: date, days: int = 5) -> date:
    """Return the next follow-up date."""
    return start + timedelta(days=days)
