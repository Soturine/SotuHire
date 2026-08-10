from __future__ import annotations

from datetime import UTC, datetime

from tests.api_test_helpers import api_client


def test_api_real_interview_star_followup_task_plan_and_ics(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    interview = client.post(
        "/api/v1/interviews",
        json={
            "interview_type": "technical",
            "organization": "Empresa Ficticia",
            "role": "Pessoa Engenheira",
            "status": "scheduled",
            "scheduled_at": "2026-08-15T11:00:00Z",
        },
    )
    assert interview.status_code == 201
    session_id = interview.json()["data"]["session_id"]

    preparation = client.post(
        f"/api/v1/interviews/{session_id}/prepare",
        json={
            "opportunity_summary": "Funcao ficticia.",
            "requirements": ["Python", "Kubernetes"],
            "evidence": [
                {
                    "title": "Projeto Python",
                    "description": "Python confirmado",
                    "source_ref": "fixture://python",
                    "confirmed_by_user": True,
                },
                {
                    "title": "Nao confirmado",
                    "description": "Kubernetes",
                    "source_ref": "fixture://candidate",
                    "confirmed_by_user": False,
                },
            ],
        },
    )
    assert preparation.status_code == 200
    assert preparation.json()["data"]["confirmed_strengths"] == ["Python"]
    assert preparation.json()["data"]["gaps"] == ["Kubernetes"]

    story = client.post(
        "/api/v1/interviews/star-stories",
        json={"title": "Historia ficticia", "evidence_refs": ["fixture://python"]},
    )
    follow_up = client.post(
        "/api/v1/interviews/follow-ups",
        json={
            "interview_session_id": session_id,
            "follow_up_type": "thank_you",
            "subject": "Obrigado",
            "body": "Rascunho manual.",
        },
    )
    task = client.post(
        "/api/v1/career/tasks",
        json={"task_type": "interview", "title": "Revisar respostas"},
    )
    task_id = task.json()["data"]["task_id"]
    reminder = client.post(
        "/api/v1/career/reminders",
        json={
            "task_id": task_id,
            "title": "Revisao",
            "remind_at": "2026-08-14T11:00:00Z",
        },
    )
    plan = client.post(
        "/api/v1/career/plans",
        json={"title": "Plano ficticio", "goals": []},
    )
    calendar = client.post(
        "/api/v1/career/calendar/export",
        json={
            "entity_type": "interview",
            "entity_id": session_id,
            "title": "Entrevista ficticia",
            "starts_at": datetime(2026, 8, 15, 11, tzinfo=UTC).isoformat(),
        },
    )

    assert story.status_code == follow_up.status_code == task.status_code == 201
    assert reminder.status_code == plan.status_code == 201
    assert follow_up.json()["data"]["status"] == "draft"
    assert calendar.status_code == 200
    assert calendar.json()["data"]["imported_automatically"] is False
    assert "BEGIN:VCALENDAR\r\n" in calendar.json()["data"]["content"]

    local_ai = client.post(
        "/api/v1/interviews/ai/interview_question_generation",
        json={
            "payload": {"evidence": ["fixture://python"]},
            "source_refs": ["fixture://python"],
            "external_ai_opt_in": False,
        },
    )
    assert local_ai.status_code == 200
    assert local_ai.json()["data"]["provider_used"] == "local"
    assert local_ai.json()["data"]["output"]["needs_user_review"] is True
