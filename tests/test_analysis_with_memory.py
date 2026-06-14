from modules.ai.providers.base import AIProvider
from modules.ai.structured_analysis import analyze_structured
from modules.memory import CareerEvidence
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class RecordingGeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        self.memory_context = ""

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
        memory_context: str = "",
    ) -> JobAnalysisSchema:
        self.memory_context = memory_context
        return JobAnalysisSchema(
            match_score=70,
            ats_score=70,
            opportunity_fit_score=70,
            risk_score=0,
            recommendation="apply_with_adjustments",
        )


def _evidence() -> list[CareerEvidence]:
    return [
        CareerEvidence(
            memory_id="project-1",
            title="Projeto FastAPI",
            source="resume",
            excerpt="API Python com FastAPI e PostgreSQL",
            relevance_score=0.9,
        )
    ]


def test_local_analysis_uses_memory_evidence():
    without_memory = analyze_structured("SQL", "Vaga Python FastAPI")
    with_memory = analyze_structured(
        "SQL",
        "Vaga Python FastAPI",
        memory_evidence=_evidence(),
    )

    assert with_memory.memory_used
    assert with_memory.evidence
    assert with_memory.analysis.match_score > without_memory.analysis.match_score


def test_gemini_does_not_receive_memory_without_explicit_flag():
    provider = RecordingGeminiProvider()

    result = analyze_structured(
        "Python",
        "Vaga Python",
        provider=provider,
        memory_evidence=_evidence(),
        share_memory_with_provider=False,
    )

    assert result.memory_used
    assert not result.memory_shared_with_provider
    assert provider.memory_context == ""


def test_gemini_receives_only_relevant_memory_when_explicitly_enabled():
    provider = RecordingGeminiProvider()

    result = analyze_structured(
        "Python",
        "Vaga Python",
        provider=provider,
        memory_evidence=_evidence(),
        share_memory_with_provider=True,
    )

    assert result.memory_shared_with_provider
    assert "Projeto FastAPI" in provider.memory_context
