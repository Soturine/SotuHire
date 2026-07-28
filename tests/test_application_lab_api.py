from __future__ import annotations

from apps.api.main import create_app
from apps.api.services.application_lab import (
    ApplicationLabApiService,
    get_application_lab_api_service,
)
from fastapi.testclient import TestClient
from modules.application_lab.models import (
    MasterResume,
    ResumeEntry,
    ResumeSection,
)
from modules.application_lab.service import ApplicationLabService
from modules.context.models import CareerContext, CareerContextPurpose
from modules.storage.snapshots import JobSnapshot


class EmptyContextEngine:
    def build(self, purpose, **kwargs) -> CareerContext:
        del kwargs
        return CareerContext(purpose=CareerContextPurpose(purpose))


def _client(tmp_path) -> tuple[TestClient, ApplicationLabApiService]:
    domain = ApplicationLabService(
        tmp_path / "sotuhire.db",
        context_engine=EmptyContextEngine(),  # type: ignore[arg-type]
    )
    service = ApplicationLabApiService(domain)
    app = create_app()
    app.dependency_overrides[get_application_lab_api_service] = lambda: service
    return TestClient(app), service


def _master() -> MasterResume:
    return MasterResume(
        master_resume_id="master-api",
        profile_id="profile-api",
        title="Currículo API Fictício",
        target_role="Analista de laboratório",
        summary="Profissional fictícia com prática de qualidade confirmada.",
        source_refs=["fixture://profile-api"],
        sections=[
            ResumeSection(
                section_type="experience",
                title="Experiência",
                entries=[
                    ResumeEntry(
                        title="Controle de qualidade",
                        content="Executou protocolo fictício sob supervisão.",
                        source_refs=["fixture://experience-api"],
                        confirmed_by_user=True,
                    )
                ],
            )
        ],
    )


def _job(service: ApplicationLabApiService) -> JobSnapshot:
    return service.domain.snapshots.create_job(
        JobSnapshot(
            snapshot_id="job-api",
            opportunity_id="opportunity-api",
            title="Analista de laboratório",
            organization="Laboratório Fictício",
            description="Controle de qualidade e protocolos.",
            source_url="https://example.invalid/job-api",
            source_refs=["fixture://job-api"],
            structured_data={"requirements": ["Controle de qualidade", "ISO 17025"]},
        )
    )


def test_application_lab_and_resume_studio_api_journey(tmp_path) -> None:
    client, service = _client(tmp_path)
    master = _master()
    job = _job(service)

    master_response = client.put(
        "/api/v1/resume-studio/master",
        json={"resume": master.model_dump(mode="json"), "request_id": "req-master"},
    )
    created = client.post(
        "/api/v1/application-lab/sessions",
        json={
            "master_resume_id": master.master_resume_id,
            "job_id": job.opportunity_id,
            "job_snapshot_id": job.snapshot_id,
            "selected_context_refs": ["fixture://experience-api"],
            "request_id": "req-session",
        },
    )

    assert master_response.status_code == 200
    assert master_response.json()["request_id"] == "req-master"
    assert created.status_code == 200
    session_id = created.json()["data"]["session"]["session_id"]
    page = client.get("/api/v1/application-lab/sessions?limit=1")
    assert page.json()["data"]["pagination"]["total"] == 1

    analyzed = client.post(f"/api/v1/application-lab/sessions/{session_id}/analyze", json={})
    assert analyzed.status_code == 200
    analysis_data = analyzed.json()["data"]
    assert len(analysis_data["progress_steps"]) == 8
    suggestion = next(item for item in analysis_data["suggestions"] if item["evidence_used"])
    accepted = client.post(
        f"/api/v1/application-lab/sessions/{session_id}/suggestions/"
        f"{suggestion['suggestion_id']}/accept",
        json={},
    )
    assert accepted.json()["data"]["status"] == "accepted"

    variant_response = client.post(
        f"/api/v1/application-lab/sessions/{session_id}/variant",
        json={"title": "Variante revisada"},
    )
    variant_id = variant_response.json()["data"]["resume_variant_id"]
    assert variant_response.status_code == 200
    assert (
        client.post(f"/api/v1/application-lab/sessions/{session_id}/kit", json={}).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/application-lab/sessions/{session_id}/action-plan",
            json={"period_days": 7},
        ).status_code
        == 200
    )
    tracker = client.post(
        f"/api/v1/application-lab/sessions/{session_id}/tracker",
        json={"privacy_acknowledged": True},
    )
    assert tracker.status_code == 200
    assert tracker.json()["data"]["session"]["status"] == "completed"

    json_export = client.post(
        f"/api/v1/resume-studio/variants/{variant_id}/export",
        json={"format": "json_resume", "template_id": "classic"},
    )
    pdf_export = client.post(
        f"/api/v1/resume-studio/variants/{variant_id}/export",
        json={"format": "pdf", "template_id": "classic"},
    )
    assert json_export.json()["data"]["export"]["status"] == "ready"
    assert json_export.json()["data"]["payload"] is not None
    assert pdf_export.json()["data"]["export"]["status"] == "pending"
    assert pdf_export.json()["data"]["payload"] is None
    assert client.get("/api/v1/resume-studio/templates").json()["data"]["items"]


def test_api_invalidates_dependent_steps_and_uses_error_envelope(tmp_path) -> None:
    client, service = _client(tmp_path)
    first = service.repository.save_master_resume(_master())
    second = service.repository.save_master_resume(
        _master().model_copy(update={"master_resume_id": "master-api-second"})
    )
    job = _job(service)
    created = client.post(
        "/api/v1/application-lab/sessions",
        json={
            "master_resume_id": first.master_resume_id,
            "job_snapshot_id": job.snapshot_id,
        },
    ).json()["data"]
    session_id = created["session"]["session_id"]
    updated = client.patch(
        f"/api/v1/application-lab/sessions/{session_id}",
        json={"master_resume_id": second.master_resume_id},
    )
    missing = client.get("/api/v1/application-lab/sessions/not-found")

    assert updated.json()["data"]["session"]["invalidated_steps"] == list(range(5, 11))
    assert missing.status_code == 404
    assert missing.json()["ok"] is False
    assert missing.json()["error"]["code"] == "http_error"


def test_openapi_exposes_all_guided_workflow_contracts(tmp_path) -> None:
    client, _ = _client(tmp_path)
    paths = client.get("/openapi.json").json()["paths"]

    expected = {
        "/api/v1/application-lab/sessions",
        "/api/v1/application-lab/sessions/{session_id}",
        "/api/v1/application-lab/sessions/{session_id}/analyze",
        "/api/v1/application-lab/sessions/{session_id}/variant",
        "/api/v1/application-lab/sessions/{session_id}/kit",
        "/api/v1/application-lab/sessions/{session_id}/action-plan",
        "/api/v1/application-lab/sessions/{session_id}/tracker",
        "/api/v1/resume-studio/master",
        "/api/v1/resume-studio/variants",
        "/api/v1/resume-studio/variants/{variant_id}",
        "/api/v1/resume-studio/variants/{variant_id}/export",
    }
    assert expected <= set(paths)
