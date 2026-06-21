from modules.ai.schemas.common import ConfidenceSummary
from modules.ai.schemas.job_extraction import (
    JobExtractionOutput,
    JobIdentity,
    JobRequirement,
)
from modules.ai.structured_job_extractor import extract_structured_job


class FakeJobProvider:
    name = "fake"

    def generate_structured(self, prompt, payload):  # noqa: ANN001, ANN201
        assert prompt.prompt_id == "job_extraction_multi_domain_v1"
        assert "job_text" in payload
        return JobExtractionOutput(
            job_identity=JobIdentity(title="Enfermeiro UTI", company="Hospital Ficticio"),
            requirements=[
                JobRequirement(
                    text="COREN ativo",
                    normalized_name="COREN",
                    category="professional_license",
                    importance="required",
                    criticality="knockout",
                    confidence=0.95,
                )
            ],
            extraction_confidence=ConfidenceSummary(overall=0.86, needs_user_review=False),
        )


class FailingProvider:
    name = "fake"

    def generate_structured(self, prompt, payload):  # noqa: ANN001, ANN201
        raise RuntimeError("invalid json")


def test_structured_job_extractor_uses_provider_output() -> None:
    result = extract_structured_job(
        "Vaga: Enfermeiro UTI\nEmpresa: Hospital Ficticio\nObrigatorio: COREN ativo",
        provider=FakeJobProvider(),
    )

    assert result.provider == "fake"
    assert not result.fallback_used
    assert result.output.requirements[0].criticality == "knockout"


def test_structured_job_extractor_falls_back_to_local_parser() -> None:
    result = extract_structured_job(
        "Vaga: Analista SOC\nRequisitos: SIEM, SOC, resposta a incidentes",
        provider=FailingProvider(),
    )

    assert result.provider == "local"
    assert result.fallback_used
    assert result.output.domain_classification.primary_domain == "cybersecurity"
    assert any(item.normalized_name == "SIEM" for item in result.output.requirements)
