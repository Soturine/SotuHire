import pytest
from modules.ai.schemas.common import ConfidenceSummary
from modules.ai.schemas.job_extraction import JobExtractionOutput, JobRequirement
from pydantic import ValidationError


def test_job_extraction_schema_validates_requirements() -> None:
    output = JobExtractionOutput(
        requirements=[
            JobRequirement(
                text="COREN ativo",
                normalized_name="COREN",
                category="professional_license",
                importance="required",
                criticality="knockout",
                evidence="COREN ativo obrigatorio",
                confidence=0.95,
            )
        ],
        extraction_confidence=ConfidenceSummary(overall=0.88, needs_user_review=False),
    )

    assert output.requirements[0].importance == "required"
    assert output.requirements[0].criticality == "knockout"


def test_job_extraction_schema_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        JobRequirement(text="CRP ativo", category="professional_license", confidence=-0.1)
