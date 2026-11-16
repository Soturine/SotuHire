"""Formatting helpers for public exam integrations."""

from __future__ import annotations

from .models import ExamRequirement


def checklist_from_requirements(requirements: list[ExamRequirement]) -> list[ExamRequirement]:
    """Return a stable checklist ordered by risk."""
    weight = {"missing": 0, "uncertain": 1, "matched": 2}
    return sorted(requirements, key=lambda item: (weight.get(item.match_status, 1), item.kind))
