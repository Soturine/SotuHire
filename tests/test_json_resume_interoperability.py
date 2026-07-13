from modules.profile.json_resume import json_resume_to_profile, profile_to_json_resume
from modules.profile.models import ProfileItem, UniversalCareerProfile
from modules.schemas.json_resume import JSONResume


def test_profile_export_only_uses_confirmed_non_sensitive_facts_by_default():
    profile = UniversalCareerProfile(
        display_name="Pessoa Exemplo",
        headline="Engenheira",
        items=[
            ProfileItem(
                type="technical_skill",
                title="Python",
                evidence="Projeto confirmado",
                source="github",
                source_ref="https://github.com/example/project",
                confirmed_by_user=True,
            ),
            ProfileItem(type="technical_skill", title="A confirmar"),
            ProfileItem(
                type="constraint",
                title="Informação sensível",
                confirmed_by_user=True,
                sensitive=True,
            ),
        ],
    )

    exported = profile_to_json_resume(profile)

    assert exported.basics["name"] == "Pessoa Exemplo"
    assert [entry["name"] for entry in exported.skills] == ["Python"]
    assert exported.evidence[0].source_ref == "https://github.com/example/project"
    assert exported.evidence[0].can_use_in_resume is True


def test_json_resume_import_creates_reviewable_candidates_without_persisting():
    imported = json_resume_to_profile(
        JSONResume(
            basics={"name": "Pessoa Exemplo", "label": "Analista"},
            work=[{"name": "Organização", "position": "Analista", "summary": "Dados"}],
            skills=[{"name": "SQL", "keywords": ["Python"]}],
        )
    )

    assert imported.display_name == "Pessoa Exemplo"
    assert {item.title for item in imported.items} == {"Analista", "SQL", "Python"}
    assert all(item.source == "json_resume" for item in imported.items)
    assert all(not item.confirmed_by_user for item in imported.items)
    assert all(item.source_ref for item in imported.items)
