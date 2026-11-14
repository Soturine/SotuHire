"""Formatting helpers for public exam integrations."""

from __future__ import annotations

from .models import ExamRequirement, ExamRole


def checklist_from_requirements(requirements: list[ExamRequirement]) -> list[ExamRequirement]:
    """Return a stable checklist ordered by risk."""
    weight = {"missing": 0, "uncertain": 1, "matched": 2}
    return sorted(requirements, key=lambda item: (weight.get(item.match_status, 1), item.kind))


def _role_summary(role: ExamRole) -> str:
    parts = [
        role.education_level,
        role.required_degree,
        role.required_registry,
        role.salary,
        role.workload,
        role.location,
    ]
    return "; ".join(part for part in parts if part)
