from __future__ import annotations

from modules.profile import (
    CareerProfileStore,
    ProfileContextOrchestrator,
    ProfileItem,
    UniversalCareerProfile,
)
from modules.profile.schemas import CareerProfile
from modules.profile.store import UniversalCareerProfileStore


def test_profile_reconciliation_uses_universal_per_bucket_and_legacy_fallback(tmp_path) -> None:
    universal = UniversalCareerProfileStore(tmp_path / "profiles.json")
    legacy = CareerProfileStore(tmp_path / "legacy.json")
    universal.save_active(
        UniversalCareerProfile(
            target_roles=["Engenharia de Dados"],
            items=[
                ProfileItem(
                    type="technical_skill",
                    title="Python",
                    confirmed_by_user=True,
                    source_ref="fixture://profile/python",
                )
            ],
        )
    )
    legacy.save(
        CareerProfile(
            target_roles=["Backend"],
            education_summary=["Graduação fictícia"],
            technical_skills=["Java"],
            experience_summary=["Experiência fictícia"],
        )
    )

    context = ProfileContextOrchestrator(
        store=legacy,
        universal_store=universal,
    ).build_context()
    decisions = {item.bucket: item for item in context.reconciliation.buckets}

    assert context.career_goals == ["Engenharia de Dados"]
    assert [item.title for item in context.education] == ["Graduação fictícia"]
    assert [item.title for item in context.experiences] == ["Experiência fictícia"]
    assert [item.title for item in context.skills] == ["Python"]
    assert decisions["education"].source == "legacy_fallback"
    assert decisions["skills"].source == "universal"
    assert decisions["skills"].conflict is True
    assert context.reconciliation.requires_review is True
