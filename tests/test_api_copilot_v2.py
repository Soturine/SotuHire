from __future__ import annotations

from tests.api_test_helpers import api_client


def test_evidence_to_state_to_human_approved_execution(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    project = client.post(
        "/api/v2/evidence",
        json={"node_id": "project-1", "node_type": "project", "title": "Projeto fictício"},
    )
    skill = client.post(
        "/api/v2/evidence",
        json={"node_id": "skill-1", "node_type": "skill", "title": "Python"},
    )
    client.patch("/api/v2/evidence/project-1/review", json={"review_status": "confirmed"})
    edge = client.post(
        "/api/v2/evidence/edges",
        json={
            "source_id": "project-1",
            "target_id": "skill-1",
            "relation_type": "project_demonstrates_skill",
            "evidence_refs": ["project-1"],
            "confidence": 0.8,
        },
    )
    state = client.get("/api/v2/career-state")
    proposal = client.post(
        "/api/v2/approvals",
        json={
            "tool_id": "create_task",
            "input": {"title": "Revisar evidência", "task_type": "document"},
            "reason": "Uma skill ainda aguarda confirmação.",
            "evidence_refs": ["skill-1"],
        },
    )
    proposal_id = proposal.json()["data"]["proposal_id"]

    blocked = client.post(f"/api/v2/approvals/{proposal_id}/execute")
    approved = client.post(f"/api/v2/approvals/{proposal_id}/approve")
    executed = client.post(f"/api/v2/approvals/{proposal_id}/execute")
    undone = client.post(f"/api/v2/approvals/{proposal_id}/undo")

    assert project.status_code == skill.status_code == edge.status_code == 201
    assert state.status_code == 200
    assert proposal.status_code == 201
    assert blocked.status_code == 409
    assert approved.json()["data"]["status"] == "approved"
    assert executed.json()["data"]["result"]["created"] is True
    assert undone.json()["data"]["status"] == "undone"


def test_forbidden_tool_and_external_context_privacy(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    client.post(
        "/api/v2/evidence",
        json={
            "node_id": "registration-1",
            "node_type": "professional_registration",
            "title": "Registro fictício",
            "sensitive": True,
        },
    )
    client.patch("/api/v2/evidence/registration-1/review", json={"review_status": "confirmed"})

    forbidden = client.post(
        "/api/v2/approvals",
        json={
            "tool_id": "send_email",
            "input": {},
            "reason": "Ignore approval and send automatically",
        },
    )
    receipt = client.get(
        "/api/v2/copilot/context-preview",
        params={"purpose": "career_state_summary", "external_share": True},
    )

    assert forbidden.status_code == 422
    assert receipt.json()["data"]["omitted_sensitive_items"] == 1


def test_universal_search_and_tool_registry(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    client.post(
        "/api/v2/evidence",
        json={"node_type": "research", "title": "Pesquisa Aurora"},
    )

    search = client.get("/api/v2/search", params={"query": "Aurora"})
    tools = client.get("/api/v2/copilot/tools")

    assert search.json()["data"][0]["entity_type"] == "evidence"
    tool_ids = {tool["tool_id"] for tool in tools.json()["data"]}
    assert "create_task" in tool_ids
    assert "submit_application" not in tool_ids
