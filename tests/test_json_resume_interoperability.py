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
    assert {item.title for item in imported.items} == {"Analista", "SQL"}
    assert next(item for item in imported.items if item.title == "SQL").skills == ["Python"]
    assert all(item.source == "json_resume" for item in imported.items)
    assert all(not item.confirmed_by_user for item in imported.items)
    assert all(item.source_ref for item in imported.items)


def test_json_resume_round_trip_preserves_sections_extensions_and_unknown_fields():
    payload = {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
        "basics": {
            "name": "Pessoa Ficticia",
            "label": "Engenheira",
            "email": "pessoa@example.invalid",
            "location": {"city": "Recife", "countryCode": "BR"},
            "profiles": [{"network": "Example", "username": "pessoa"}],
        },
        "work": [{"name": "Empresa Exemplo", "position": "Engenheira", "x-extra": 1}],
        "volunteer": [{"organization": "ONG Exemplo", "position": "Mentora"}],
        "education": [{"institution": "Universidade Exemplo", "studyType": "Bacharelado"}],
        "awards": [{"title": "Premio Exemplo", "awarder": "Instituto Exemplo"}],
        "certificates": [{"name": "Certificacao Exemplo", "issuer": "Emissor Exemplo"}],
        "publications": [{"name": "Artigo Exemplo", "publisher": "Revista Exemplo"}],
        "skills": [{"name": "Python", "level": "avancado", "keywords": ["FastAPI"]}],
        "languages": [{"language": "Portugues", "fluency": "nativo"}],
        "interests": [{"name": "Dados abertos", "keywords": ["governo"]}],
        "references": [{"name": "Referencia Ficticia", "reference": "Recomendacao"}],
        "projects": [{"name": "Projeto Exemplo", "description": "Projeto local"}],
        "meta": {"canonical": "fixture://resume"},
        "x-sotuhire": {
            "professionalRegistrations": [
                {"name": "Registro Profissional 123", "authority": "Conselho Exemplo"}
            ],
            "futureField": {"preserve": True},
        },
        "evidence": [
            {
                "fact": "Python",
                "source": "fixture",
                "evidence": "Projeto ficticio",
                "confidence": 0.8,
            }
        ],
        "customSection": [{"name": "Campo futuro", "value": 42}],
    }

    profile = json_resume_to_profile(payload)
    exported = profile_to_json_resume(profile, confirmed_only=False).model_dump(
        mode="json", by_alias=True
    )

    expected_sections = {
        "work",
        "volunteer",
        "education",
        "awards",
        "certificates",
        "publications",
        "skills",
        "languages",
        "interests",
        "references",
        "projects",
    }
    assert all(exported[section] for section in expected_sections)
    assert exported["work"][0]["x-extra"] == 1
    assert exported["basics"]["location"] == {"city": "Recife", "countryCode": "BR"}
    assert exported["customSection"] == payload["customSection"]
    assert exported["meta"] == payload["meta"]
    assert exported["x-sotuhire"]["futureField"] == {"preserve": True}
    registrations = exported["x-sotuhire"]["professionalRegistrations"]
    assert registrations[0]["name"] == "Registro Profissional 123"
    assert all(item["name"] != "Registro Profissional 123" for item in exported["certificates"])
    assert any(item["source"] == "fixture" for item in exported["evidence"])
    assert all(not item.confirmed_by_user for item in profile.items)
