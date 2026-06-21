import pytest
from modules.ai.schemas.common import ConfidenceSummary
from modules.ai.schemas.resume_extraction import (
    CandidateIdentity,
    ExtractedSkill,
    ResumeExtractionOutput,
)
from pydantic import ValidationError


def test_resume_extraction_schema_validates_main_fields() -> None:
    output = ResumeExtractionOutput(
        candidate_identity=CandidateIdentity(
            name="Pessoa Ficticia",
            email_present=True,
            phone_present=False,
            confidence=0.9,
        ),
        skills=[
            ExtractedSkill(
                name="AutoCAD",
                normalized_name="AutoCAD",
                category="software",
                evidence=["AutoCAD em projetos academicos"],
                confidence=0.84,
            )
        ],
        extraction_confidence=ConfidenceSummary(overall=0.8, needs_user_review=False),
    )

    assert output.candidate_identity.name == "Pessoa Ficticia"
    assert output.skills[0].category == "software"


def test_resume_extraction_schema_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        ExtractedSkill(name="COREN", category="professional_license", confidence=1.2)
