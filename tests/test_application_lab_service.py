from __future__ import annotations

from modules.application_lab.export import prepare_resume_export
from modules.application_lab.models import (
    ApplicationLabSession,
    ApplicationLabStatus,
    ApplicationSuggestion,
    MasterResume,
    ResumeEntry,
    ResumeSection,
)
from modules.application_lab.service import ApplicationLabService
from modules.context.models import CareerContext, CareerContextPurpose
from modules.storage.applications import ApplicationRepository
from modules.storage.snapshots import JobSnapshot, SnapshotStore


class EmptyContextEngine:
    def build(self, purpose, **kwargs) -> CareerContext:
        del kwargs
        return CareerContext(purpose=CareerContextPurpose(purpose))


def _master(identifier: str = "master-lab") -> MasterResume:
    return MasterResume(
        master_resume_id=identifier,
        profile_id="profile-fixture",
        title="Currículo Fictício",
        target_role="Engenharia de processos",
        summary="Profissional fictícia com experiência supervisionada.",
        source_refs=["fixture://profile"],
        source_profile_item_ids=["profile-item-fixture"],
        sections=[
            ResumeSection(
                section_id=f"section-{identifier}",
                section_type="experience",
                title="Experiência",
                entries=[
                    ResumeEntry(
                        entry_id=f"entry-{identifier}",
                        title="Prática supervisionada",
                        content="Aplicação de protocolos de qualidade em ambiente fictício.",
                        source_profile_item_ids=["profile-item-fixture"],
                        source_refs=["fixture://experience"],
                        confirmed_by_user=True,
                    ),
                    ResumeEntry(
                        title="Candidato não confirmado",
                        content="Conteúdo ainda sem confirmação.",
                    ),
                ],
            )
        ],
    )


def _job(store: SnapshotStore, identifier: str = "job-lab") -> JobSnapshot:
    return store.create_job(
        JobSnapshot(
            snapshot_id=identifier,
            opportunity_id=f"opportunity-{identifier}",
            title="Analista de qualidade",
            organization="Empresa Fictícia",
            location="Híbrido",
            description="Protocolos de qualidade e melhoria de processos.",
            source_url=f"https://example.invalid/jobs/{identifier}",
            source_refs=[f"fixture://{identifier}"],
            structured_data={"requirements": ["Protocolos de qualidade", "Lean Six Sigma"]},
        )
    )


def _service(tmp_path) -> ApplicationLabService:
    return ApplicationLabService(
        tmp_path / "sotuhire.db",
        context_engine=EmptyContextEngine(),  # type: ignore[arg-type]
    )


def test_full_application_lab_journey_links_snapshots_and_tracker(tmp_path) -> None:
    service = _service(tmp_path)
    master = service.repository.save_master_resume(_master())
    job = _job(service.snapshots)
    session = service.create_session(
        ApplicationLabSession(
            session_id="session-lab",
            profile_id=master.profile_id,
            master_resume_id=master.master_resume_id,
            job_id=job.opportunity_id,
            job_snapshot_id=job.snapshot_id,
            selected_context_refs=["fixture://experience"],
        )
    )

    assert session.status is ApplicationLabStatus.READY
    report, suggestions, analysis_snapshot = service.analyze(session.session_id)
    assert report.readiness_score >= 0
    assert analysis_snapshot.analysis_type == "application_readiness"
    assert suggestions

    evidence_suggestion = next(item for item in suggestions if item.evidence_used)
    reviewed = service.review_suggestion(
        session.session_id, evidence_suggestion.suggestion_id, "accepted"
    )
    assert reviewed.status == "accepted"
    variant = service.create_variant(session.session_id)
    assert variant.change_set
    assert variant.sections != master.sections
    assert service.repository.get_master_resume(master.master_resume_id) == master

    kit, kit_snapshot = service.create_kit(session.session_id)
    assert kit.items
    assert kit_snapshot.analysis_type == "application_kit"
    plan = service.create_action_plan(session.session_id, period_days=14)
    assert plan.period_days == 14

    tracker_id = service.save_to_tracker(
        session.session_id,
        privacy_acknowledged=True,
        source_capture_id="capture-fixture",
    )
    completed = service.repository.get_session(session.session_id)
    application = ApplicationRepository(tmp_path / "sotuhire.db").get(tracker_id)
    assert completed is not None and completed.status is ApplicationLabStatus.COMPLETED
    assert application is not None
    assert application.application_lab_session_id == session.session_id
    assert application.readiness_report_id == report.report_id
    assert application.resume_variant_id == variant.resume_variant_id
    assert application.application_kit_id == kit.application_kit_id
    assert application.action_plan_id == plan.action_plan_id
    assert application.lab_analysis_snapshot_id == analysis_snapshot.snapshot_id
    assert application.application_kit_snapshot_id == kit_snapshot.snapshot_id
    assert service.snapshots.get_job(application.job_snapshot_id) == job


def test_input_change_invalidates_dependents_but_keeps_review_decisions(tmp_path) -> None:
    service = _service(tmp_path)
    first_master = service.repository.save_master_resume(_master())
    second_master = service.repository.save_master_resume(_master("master-second"))
    job = _job(service.snapshots)
    session = service.create_session(
        ApplicationLabSession(
            master_resume_id=first_master.master_resume_id,
            job_snapshot_id=job.snapshot_id,
        )
    )
    _, suggestions, _ = service.analyze(session.session_id)
    accepted = next(item for item in suggestions if item.evidence_used)
    service.review_suggestion(session.session_id, accepted.suggestion_id, "accepted")
    service.create_variant(session.session_id)

    updated = service.update_session(
        session.session_id, {"master_resume_id": second_master.master_resume_id}
    )

    assert updated.invalidated_steps == list(range(5, 11))
    assert not updated.readiness_report_id
    assert not updated.resume_variant_id
    preserved = service.repository.get_suggestion(accepted.suggestion_id)
    assert preserved is not None and preserved.status == "accepted"


def test_unsupported_claim_cannot_be_accepted_and_session_can_be_cancelled(tmp_path) -> None:
    service = _service(tmp_path)
    master = service.repository.save_master_resume(_master())
    job = _job(service.snapshots)
    session = service.create_session(
        ApplicationLabSession(
            master_resume_id=master.master_resume_id,
            job_snapshot_id=job.snapshot_id,
        )
    )
    unsupported = ApplicationSuggestion(
        suggestion_id="unsupported",
        session_id=session.session_id,
        suggestion_type="claim",
        after="Afirmação inventada",
    )
    service.repository.save_suggestions([unsupported])

    try:
        service.review_suggestion(session.session_id, unsupported.suggestion_id, "accepted")
    except ValueError as exc:
        assert "evidência" in str(exc)
    else:
        raise AssertionError("A claim sem evidência foi aceita")

    cancelled = service.cancel_session(session.session_id)
    assert cancelled.status is ApplicationLabStatus.CANCELLED


def test_json_resume_is_functional_and_other_exports_are_explicitly_pending() -> None:
    master = _master()

    ready, payload = prepare_resume_export(master, export_format="json_resume")
    pending, no_payload = prepare_resume_export(master, export_format="pdf")

    assert ready.status == "ready"
    assert ready.content_hash
    assert payload is not None and payload["work"]
    assert "Conteúdo ainda sem confirmação." not in str(payload)
    assert pending.status == "pending"
    assert pending.warnings and no_payload is None
