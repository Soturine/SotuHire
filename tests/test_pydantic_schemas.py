from pydantic import ValidationError

from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.json_resume import CareerEvidence, JSONResume


def test_job_analysis_schema_validates_score_range():
    try:
        JobAnalysisSchema(
            match_score=120,
            ats_score=80,
            opportunity_fit_score=70,
            risk_score=10,
            recommendation="apply",
        )
    except ValidationError:
        return
    raise AssertionError("Expected validation error for score > 100")


def test_json_resume_accepts_evidence_metadata():
    resume = JSONResume(
        basics={"name": "Pessoa Exemplo"},
        evidence=[
            CareerEvidence(
                fact="Projeto com Python",
                source="github",
                evidence="README.md",
                confidence=0.9,
            )
        ],
    )
    assert resume.evidence[0].can_use_in_resume
