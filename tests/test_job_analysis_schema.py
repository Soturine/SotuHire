import pytest
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput, TailoredResumeSection
from pydantic import ValidationError


def valid_analysis_data() -> dict[str, object]:
    return {
        "match_score": 80,
        "ats_score": 75,
        "opportunity_fit_score": 90,
        "risk_score": 10,
        "recommendation": "apply",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("match_score", -1),
        ("ats_score", 101),
        ("opportunity_fit_score", -20),
        ("risk_score", 150),
    ],
)
def test_job_analysis_rejects_scores_outside_range(field: str, value: int):
    data = valid_analysis_data()
    data[field] = value

    with pytest.raises(ValidationError):
        JobAnalysisSchema.model_validate(data)


def test_job_analysis_rejects_unknown_recommendation():
    data = valid_analysis_data()
    data["recommendation"] = "auto_apply"

    with pytest.raises(ValidationError):
        JobAnalysisSchema.model_validate(data)


def test_resume_tailor_rejects_invented_information():
    with pytest.raises(ValidationError):
        TailoredResumeSection.model_validate(
            {
                "section_name": "Experiência",
                "original_text": "Projeto acadêmico em Python",
                "tailored_text": "Cinco anos de experiência profissional em Python",
                "reason_for_change": "Aumentar aderência",
                "evidence_source": "currículo mestre",
                "invented_information": True,
            }
        )


def test_resume_tailor_accepts_evidence_backed_section():
    section = TailoredResumeSection(
        section_name="Projetos",
        original_text="API em Python com testes",
        tailored_text="Projeto de API em Python com testes automatizados",
        reason_for_change="Destacar evidência relevante",
        evidence_source="currículo mestre",
    )
    output = ResumeTailorOutput(target_role="Backend Python", tailored_sections=[section])

    assert output.is_safe_to_export()
