"""Formatting helpers for public exam integrations."""

from __future__ import annotations

from modules.context.models import CareerContextEvidence

from .models import ExamNotice, ExamRequirement, ExamRole


def notice_context_evidence(notice: ExamNotice) -> list[CareerContextEvidence]:
    """Return review-safe evidence describing a saved public exam notice."""
    evidence = [
        CareerContextEvidence(
            title=notice.title or "Edital salvo",
            content=f"{notice.organization} {notice.exam_board}".strip(),
            kind="public_exam_notice",
            source=notice.source_url or notice.source_name or "public_exams",
            confidence="medium",
            confirmed_by_user=True,
            metadata={"notice_id": notice.notice_id, "opportunity_type": notice.opportunity_type},
        )
    ]
    for role in notice.roles[:5]:
        evidence.append(
            CareerContextEvidence(
                title=role.title,
                content=_role_summary(role),
                kind="public_exam_role",
                source=notice.source_url or notice.source_name or "public_exams",
                confidence="medium",
                confirmed_by_user=True,
                metadata={"notice_id": notice.notice_id, "role_id": role.role_id},
            )
        )
    return evidence


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
