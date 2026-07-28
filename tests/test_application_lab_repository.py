from __future__ import annotations

from datetime import UTC, datetime, timedelta

from modules.application_lab.models import (
    ActionPlanItem,
    ApplicationActionPlan,
    ApplicationKit,
    ApplicationKitItem,
    ApplicationLabSession,
    ApplicationLabStatus,
    ApplicationSuggestion,
    MasterResume,
    ResumeEntry,
    ResumeSection,
    ResumeVariant,
    ResumeVariantChange,
    SuggestionStatus,
)
from modules.application_lab.readiness import build_readiness_report
from modules.application_lab.repository import ApplicationLabRepository
from modules.storage.snapshots import JobSnapshot, SnapshotStore


def _master() -> MasterResume:
    return MasterResume(
        master_resume_id="master-fixture",
        profile_id="profile-fixture",
        title="Currículo fictício",
        target_role="Enfermagem assistencial",
        summary="Profissional fictícia com registro confirmado e prática supervisionada.",
        source_type="manual",
        source_refs=["fixture://profile"],
        sections=[
            ResumeSection(
                section_id="education-section",
                section_type="education",
                title="Formação",
                position=0,
                entries=[
                    ResumeEntry(
                        entry_id="education-entry",
                        title="Bacharelado fictício em Enfermagem",
                        content="Formação concluída em instituição fictícia.",
                        source_refs=["fixture://education"],
                        confirmed_by_user=True,
                    )
                ],
            ),
            ResumeSection(
                section_id="experience-section",
                section_type="experience",
                title="Experiência",
                position=1,
                entries=[
                    ResumeEntry(
                        entry_id="experience-entry",
                        title="Estágio supervisionado fictício",
                        content="Prática supervisionada em clínica médica.",
                        source_refs=["fixture://experience"],
                        confirmed_by_user=True,
                    )
                ],
            ),
            ResumeSection(
                section_id="skills-section",
                section_type="skills",
                title="Competências",
                position=2,
                entries=[
                    ResumeEntry(
                        entry_id="skills-entry",
                        title="Segurança do paciente",
                        content="Protocolos e registros de enfermagem.",
                        source_refs=["fixture://skills"],
                        confirmed_by_user=True,
                    )
                ],
            ),
        ],
    )


def _job(database) -> JobSnapshot:
    return SnapshotStore(database).create_job(
        JobSnapshot(
            snapshot_id="job-fixture",
            opportunity_id="opportunity-fixture",
            title="Enfermeira assistencial",
            organization="Hospital Fictício",
            description="Atuação em clínica médica e segurança do paciente.",
            source_refs=["fixture://job"],
            structured_data={
                "requirements": [
                    "Bacharelado em Enfermagem",
                    "Segurança do paciente",
                    "Registro profissional ativo",
                ]
            },
        )
    )


def test_master_resume_round_trip_and_templates(tmp_path) -> None:
    repository = ApplicationLabRepository(tmp_path / "sotuhire.db")

    saved = repository.save_master_resume(_master())
    restored = repository.get_master_resume(saved.master_resume_id)

    assert restored == saved
    assert [item.template_id for item in repository.list_templates()] == [
        "academic",
        "classic",
        "compact",
        "technical",
    ]


def test_session_report_suggestions_variant_kit_and_plan_round_trip(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    repository = ApplicationLabRepository(database)
    master = repository.save_master_resume(_master())
    job = _job(database)
    session = repository.save_session(
        ApplicationLabSession(
            session_id="session-fixture",
            profile_id=master.profile_id,
            master_resume_id=master.master_resume_id,
            job_id=job.opportunity_id,
            job_snapshot_id=job.snapshot_id,
            current_step=5,
            status=ApplicationLabStatus.READY,
            selected_context_refs=["fixture://profile", "fixture://profile", ""],
        )
    )

    report = repository.save_report(build_readiness_report(session.session_id, master, job))
    suggestion = ApplicationSuggestion(
        suggestion_id="suggestion-fixture",
        session_id=session.session_id,
        suggestion_type="bullet",
        section="Experiência",
        before="Prática supervisionada.",
        after="Aplicou protocolos de segurança do paciente em prática supervisionada.",
        reason="Alinhar evidência confirmada ao requisito.",
        evidence_used=["fixture://experience"],
        source_refs=["fixture://experience"],
    )
    repository.save_suggestions([suggestion])
    reviewed = repository.review_suggestion(
        suggestion.suggestion_id,
        SuggestionStatus.EDITED,
        edited_value="Aplicou protocolos confirmados em prática supervisionada.",
    )
    variant = repository.save_variant(
        ResumeVariant(
            resume_variant_id="variant-fixture",
            master_resume_id=master.master_resume_id,
            job_snapshot_id=job.snapshot_id,
            title="Variante clínica",
            target_role=job.title,
            sections=master.sections,
            change_set=[
                ResumeVariantChange(
                    change_id="change-fixture",
                    change_type="edited",
                    section="Experiência",
                    before=suggestion.before,
                    after=reviewed.edited_value if reviewed else "",
                    reason=suggestion.reason,
                    evidence_used=suggestion.evidence_used,
                    source_refs=suggestion.source_refs,
                )
            ],
        )
    )
    kit = repository.save_kit(
        ApplicationKit(
            application_kit_id="kit-fixture",
            session_id=session.session_id,
            items=[
                ApplicationKitItem(
                    item_id="kit-item-fixture",
                    type="short_form_text",
                    content=master.summary,
                    evidence_used=["fixture://profile"],
                )
            ],
        )
    )
    plan = repository.save_action_plan(
        ApplicationActionPlan(
            action_plan_id="plan-fixture",
            session_id=session.session_id,
            period_days=7,
            items=[
                ActionPlanItem(
                    action_item_id="action-fixture",
                    title="Confirmar registro profissional",
                    related_gap="Registro profissional ativo",
                    due_at=datetime.now(UTC) + timedelta(days=2),
                )
            ],
        )
    )

    restored_session = repository.get_session(session.session_id)
    assert restored_session is not None
    assert restored_session.selected_context_refs == ["fixture://profile"]
    assert repository.get_report(report.report_id) == report
    assert reviewed is not None and reviewed.status is SuggestionStatus.EDITED
    assert repository.get_variant(variant.resume_variant_id) == variant
    assert repository.get_kit(kit.application_kit_id) == kit
    assert repository.get_action_plan(plan.action_plan_id) == plan


def test_readiness_is_deterministic_and_github_is_not_applicable_to_nursing(tmp_path) -> None:
    database = tmp_path / "sotuhire.db"
    repository = ApplicationLabRepository(database)
    master = repository.save_master_resume(_master())
    job = _job(database)

    first = build_readiness_report("session-one", master, job)
    second = build_readiness_report("session-two", master, job)

    assert first.readiness_score == second.readiness_score
    assert first.source_dimensions["github"].status == "not_applicable"
    assert first.source_dimensions["github"].weight == 0
    assert first.requirement_coverage == 0.667
    assert set(first.perspectives) == {
        "structure_ats",
        "narrative_positioning",
        "evidence_differentiators",
    }
    assert "probabilidade" in first.warnings[0].casefold()


def test_suggestion_without_evidence_stays_reviewable_with_warning() -> None:
    suggestion = ApplicationSuggestion(
        session_id="session-fixture",
        suggestion_type="claim",
        after="Afirmativa não confirmada",
    )

    assert suggestion.status is SuggestionStatus.PENDING
    assert suggestion.warnings == ["Sem evidência confirmada; não aceitar como fato."]
