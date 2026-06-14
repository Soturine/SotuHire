from modules.ai.resume_extraction import extract_resume_profile
from modules.schemas.resume_profile import ResumeProfileSchema


def test_ai_resume_extraction_merges_explicit_facts_with_local_parser():
    result = extract_resume_profile(
        "Rafa Example\nSkills: Python\nExperiência: Projeto local",
        provider="gemini",
        generator=lambda _text: ResumeProfileSchema(
            name="Rafa Example",
            skills=["Python", "SQL"],
            experiences=["Projeto local"],
        ),
    )

    assert result.provider == "gemini"
    assert result.fallback_used is False
    assert result.profile.skills == ["Python", "SQL"]
    assert result.profile.raw_text


def test_ai_resume_extraction_falls_back_to_local_parser():
    def fail(_text):
        raise RuntimeError("offline")

    result = extract_resume_profile("Skills: Python", provider="gemini", generator=fail)

    assert result.provider == "local"
    assert result.fallback_used is True
    assert "Python" in result.profile.skills
