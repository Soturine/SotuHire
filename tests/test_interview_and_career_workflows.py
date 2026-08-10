from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from modules.career_actions import (
    CareerAction,
    CareerGoal,
    CareerPlan,
    CareerTask,
    CertificationRecommendation,
    GapProject,
    Reminder,
    export_ics_event,
)
from modules.interviews import (
    FollowUpDraft,
    InterviewDraftAnswer,
    InterviewQuestion,
    InterviewSession,
    StarStory,
    prepare_interview_local,
)
from modules.storage import CareerWorkflowRepository
from pydantic import ValidationError


def test_interview_preparation_uses_only_confirmed_evidence_and_persists(tmp_path: Path) -> None:
    repository = CareerWorkflowRepository(tmp_path / "sotuhire.db")
    session = repository.save_interview(
        InterviewSession(
            interview_type="technical",
            organization="Empresa Ficticia",
            role="Pessoa Engenheira",
            status="scheduled",
            scheduled_at=datetime(2026, 8, 15, 14, tzinfo=UTC),
        )
    )
    preparation = prepare_interview_local(
        session,
        opportunity_summary="Funcao ficticia de dados.",
        requirements=["Python", "Kubernetes"],
        confirmed_evidence=[
            {
                "title": "Projeto Python",
                "description": "API Python confirmada",
                "source_ref": "fixture://profile/python",
            }
        ],
    )
    repository.save_preparation(preparation)

    restored = repository.get_preparation(session.session_id)
    assert restored is not None
    assert restored.confirmed_strengths == ["Python"]
    assert restored.gaps == restored.needs_confirmation == ["Kubernetes"]
    assert restored.evidence_refs == ["fixture://profile/python"]
    assert all("resposta" not in value.casefold() for value in restored.technical_questions)


def test_star_and_draft_answers_require_evidence_for_ai_claims() -> None:
    with pytest.raises(ValidationError, match="evidencia"):
        StarStory(
            title="Historia candidata",
            result="Aumentou 42%",
            generated_by="ai",
        )
    with pytest.raises(ValidationError, match="evidencia"):
        InterviewDraftAnswer(question_id="question-1", content="Resposta pronta")

    story = StarStory(
        title="Historia confirmada",
        result="Resultado 42 conforme fonte.",
        evidence_refs=["fixture://evidence/42"],
        generated_by="ai",
    )
    answer = InterviewDraftAnswer(
        question_id="question-1",
        content="Resposta baseada no projeto confirmado.",
        evidence_refs=["fixture://evidence/project"],
    )
    assert story.review_status == "candidate"
    assert answer.status == "draft"


def test_repository_round_trips_star_questions_followup_tasks_reminders_and_plan(
    tmp_path: Path,
) -> None:
    repository = CareerWorkflowRepository(tmp_path / "sotuhire.db")
    session = repository.save_interview(InterviewSession(interview_type="behavioral"))
    story = repository.save_star_story(
        StarStory(title="Projeto ficticio", evidence_refs=["fixture://project"])
    )
    question = repository.save_question(
        InterviewQuestion(
            session_id=session.session_id,
            category="project",
            question="Qual projeto melhor demonstra esta competencia?",
        )
    )
    answer = repository.save_answer(
        InterviewDraftAnswer(
            question_id=question.question_id,
            content="O projeto ficticio.",
            evidence_refs=["fixture://project"],
        )
    )
    follow_up = repository.save_follow_up(
        FollowUpDraft(
            interview_session_id=session.session_id,
            follow_up_type="thank_you",
            subject="Agradecimento",
            body="Rascunho para revisao manual.",
        )
    )
    task = repository.save_task(CareerTask(task_type="interview", title="Revisar perguntas"))
    reminder = repository.save_reminder(
        Reminder(
            task_id=task.task_id,
            title="Entrevista",
            remind_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    plan = repository.save_career_plan(
        CareerPlan(
            title="Plano ficticio",
            goals=[
                CareerGoal(
                    title="Praticar entrevistas",
                    horizon="30_days",
                    actions=[CareerAction(title="Revisar STAR")],
                )
            ],
            certifications=[
                CertificationRecommendation(
                    name="Certificacao ficticia",
                    classification="useful",
                    source_status="needs_source",
                )
            ],
            gap_projects=[
                GapProject(
                    domain="tecnologia",
                    gap="Observabilidade",
                    objective="Produzir evidencia revisavel",
                    deliverables=["Dashboard local"],
                    evidence_to_produce=["README e testes"],
                )
            ],
        )
    )

    assert repository.list_star_stories()[0].story_id == story.story_id
    assert (
        repository.list_questions(session_id=session.session_id)[0].question_id
        == question.question_id
    )
    assert (
        repository.list_answers(question_id=question.question_id)[0].answer_id == answer.answer_id
    )
    assert repository.list_follow_ups()[0].follow_up_id == follow_up.follow_up_id
    assert repository.list_tasks()[0].task_id == task.task_id
    assert repository.list_reminders()[0].reminder_id == reminder.reminder_id
    assert repository.list_career_plans()[0].plan_id == plan.plan_id
    assert follow_up.status == "draft"


def test_ics_has_stable_uid_crlf_timezone_and_no_automatic_method() -> None:
    start = datetime(2026, 8, 15, 11, tzinfo=UTC)
    first = export_ics_event(
        entity_type="interview",
        entity_id="fixture-1",
        title="Entrevista, etapa tecnica",
        starts_at=start,
        description="Revisar; nao enviar automaticamente",
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    second = export_ics_event(
        entity_type="interview",
        entity_id="fixture-1",
        title="Entrevista, etapa tecnica",
        starts_at=start,
        generated_at=datetime(2026, 8, 11, tzinfo=UTC),
    )

    uid_first = next(line for line in first.split("\r\n") if line.startswith("UID:"))
    uid_second = next(line for line in second.split("\r\n") if line.startswith("UID:"))
    assert uid_first == uid_second
    assert "DTSTART:20260815T110000Z" in first
    assert "SUMMARY:Entrevista\\, etapa tecnica" in first
    assert "METHOD:" not in first
    assert "\r\n" in first and not first.replace("\r\n", "").count("\n")
    with pytest.raises(ValueError, match="timezone"):
        export_ics_event(
            entity_type="task",
            entity_id="fixture-2",
            title="Sem timezone",
            starts_at=datetime(2026, 8, 15, 11),
        )
