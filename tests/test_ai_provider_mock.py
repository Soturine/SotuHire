from modules.ai.providers.gemini_provider import GeminiProvider
from modules.ai.providers.mock_provider import MockProvider
from modules.ai.structured_analysis import analyze_structured
from modules.schemas.job_analysis import JobAnalysisSchema


def test_mock_provider_returns_valid_schema():
    result = MockProvider().analyze(
        "Resumo\nPython SQL\nExperiencia\nProjeto de API.",
        "Vaga Python SQL remota para pessoa junior.",
    )

    assert isinstance(result, JobAnalysisSchema)
    assert 0 <= result.match_score <= 100


def test_structured_analysis_falls_back_when_gemini_has_no_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = analyze_structured("Python", "Vaga Python", provider=GeminiProvider(api_key=""))

    assert result.provider == "mock"
    assert result.fallback_used
    assert isinstance(result.analysis, JobAnalysisSchema)
