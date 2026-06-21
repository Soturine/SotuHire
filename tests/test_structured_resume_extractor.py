from modules.ai.schemas.common import ConfidenceSummary
from modules.ai.schemas.resume_extraction import (
    CandidateIdentity,
    ResumeExtractionOutput,
)
from modules.ai.structured_resume_extractor import extract_structured_resume


class FakeResumeProvider:
    name = "fake"

    def generate_structured(self, prompt, payload):  # noqa: ANN001, ANN201
        assert prompt.prompt_id == "resume_extraction_v1"
        assert "resume_text" in payload
        return ResumeExtractionOutput(
            candidate_identity=CandidateIdentity(
                name="Pessoa Ficticia",
                email="pessoa@example.test",
                email_present=True,
                phone_present=False,
                confidence=0.9,
            ),
            extraction_confidence=ConfidenceSummary(overall=0.85, needs_user_review=False),
        )


class FailingProvider:
    name = "fake"

    def generate_structured(self, prompt, payload):  # noqa: ANN001, ANN201
        raise RuntimeError("provider down")


def test_structured_resume_extractor_uses_provider_output() -> None:
    result = extract_structured_resume(
        "Pessoa Ficticia\nEmail: pessoa@example.test\nSkills: Python",
        provider=FakeResumeProvider(),
    )

    assert result.provider == "fake"
    assert not result.fallback_used
    assert result.output.candidate_identity.email_present


def test_structured_resume_extractor_falls_back_to_local_parser() -> None:
    result = extract_structured_resume(
        "Pessoa Ficticia\npessoa@example.test\nCompetencias: Python, SQL",
        provider=FailingProvider(),
    )

    assert result.provider == "local"
    assert result.fallback_used
    assert result.output.candidate_identity.email_present
    assert "provider down" in result.warning
