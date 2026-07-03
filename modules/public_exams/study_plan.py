"""Initial study plan drafts for public exams."""

from __future__ import annotations

from datetime import date, datetime

from .models import ExamNotice, ExamRole, ExamSubject, StudyPlanDraft


def build_study_plan(
    notice: ExamNotice,
    role: ExamRole | None = None,
    *,
    weekly_hours: int = 8,
) -> StudyPlanDraft:
    """Build a simple, transparent study plan draft."""
    subjects = role.subjects if role and role.subjects else notice.subjects
    subjects = subjects or [ExamSubject(name="Conteúdo programático a revisar")]
    days_until_exam = _days_until(notice.timeline.exam_date)
    sorted_subjects = sorted(
        subjects,
        key=lambda subject: (0 if subject.priority == "high" else 1, -len(subject.topics)),
    )
    priority_topics = []
    for subject in sorted_subjects:
        if subject.topics:
            priority_topics.extend([f"{subject.name}: {topic}" for topic in subject.topics[:4]])
        else:
            priority_topics.append(subject.name)
    warnings = [
        "Plano inicial: ajuste manualmente conforme edital oficial, banca e sua rotina.",
        "O plano não promete aprovação e não substitui leitura do edital.",
    ]
    if days_until_exam is None:
        warnings.append("Data de prova ausente; gerei prioridade sem calendário.")
    elif days_until_exam < 30:
        warnings.append("Prazo curto até a prova; revise viabilidade e carga semanal.")
    return StudyPlanDraft(
        days_until_exam=days_until_exam,
        weekly_hours=weekly_hours,
        subjects=sorted_subjects,
        priority_topics=priority_topics[:20],
        schedule_blocks=_blocks(sorted_subjects, weekly_hours),
        warnings=warnings,
    )


def _blocks(subjects: list[ExamSubject], weekly_hours: int) -> list[str]:
    if not subjects:
        return []
    hours = max(1, weekly_hours)
    per_subject = max(1, hours // len(subjects))
    blocks = []
    for subject in subjects[:8]:
        extra = " + revisão" if subject.priority == "high" else ""
        blocks.append(f"Semana: {per_subject}h para {subject.name}{extra}.")
    remainder = hours % len(subjects)
    if remainder:
        blocks.append(f"Reserva: {remainder}h para simulados, leitura do edital e revisão.")
    return blocks


def _days_until(value: str) -> int | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            return max(0, (parsed - date.today()).days)
        except ValueError:
            continue
    return None
