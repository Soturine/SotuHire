from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.ai.providers.mock_provider import MockProvider
from modules.github_analyzer.analyzer_service import (
    analyze_github_repository as real_github_analysis,
)
from modules.portfolio.schemas import ProjectAnalysisPayload
from modules.schemas.user_preferences import UserPreferences
from tests.api_test_helpers import JOB_TEXT, RESUME_TEXT, api_client

FAKE_KEY = "test-gemini-routing-key"


class FakeGeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or ""
        self.model = model or "gemini-test-model"

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
        memory_context: str = "",
    ):
        return MockProvider().analyze(
            resume_text,
            job_text,
            preferences,
            job_details,
            memory_context=memory_context,
        )

    def generate_structured(self, prompt, payload: dict[str, object]):
        if prompt.prompt_id == "match_analysis_evidence_based_v1":
            return self.analyze(
                str(payload.get("resume_text", "")),
                str(payload.get("job_text", "")),
            )
        if prompt.prompt_id == "ats_analysis_v1":
            return {
                "keyword_observations": ["Python aparece como evidencia direta."],
                "safe_to_add_if_true": ["Docker pode ser destacado se for verdadeiro."],
                "missing_without_evidence": ["Kubernetes"],
                "warnings": ["Nao adicionar Kubernetes sem evidencia."],
                "confidence": 0.72,
            }
        if prompt.prompt_id == "resume_tailor_v1":
            return {
                "safe_keywords": ["Python", "FastAPI"],
                "suggested_bullets": [
                    "Destacar APIs em Python/FastAPI quando isso estiver no curriculo."
                ],
                "conditional_suggestions": ["Mencionar Docker apenas se houver experiencia real."],
                "warnings": ["Revise antes de exportar."],
                "evidence_used": ["Python", "FastAPI"],
                "confidence": 0.74,
            }
        return prompt.output_schema()


class FailingGeminiProvider(FakeGeminiProvider):
    def generate_structured(self, prompt, payload: dict[str, object]):
        raise RuntimeError("provider unavailable")


def _save_gemini_settings(client, **overrides: Any) -> None:
    payload = {
        "provider": "gemini",
        "model": "gemini-test-model",
        "api_key": FAKE_KEY,
        "use_ai": True,
        "allow_match": True,
        "allow_ats": True,
        "allow_tailor": True,
        "allow_github": True,
        "allow_memory_context": False,
    }
    payload.update(overrides)
    response = client.post(
        "/api/v1/settings/ai",
        json=payload,
    )
    assert response.status_code == 200


def test_match_uses_backend_gemini_runtime_without_returning_key(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FakeGeminiProvider)
    client = api_client()
    _save_gemini_settings(client)

    response = client.post(
        "/api/v1/match/analyze",
        json={"resume_text": RESUME_TEXT, "job_text": JOB_TEXT},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["provider_used"] == "gemini"
    assert payload["data"]["analysis_mode"] == "ai"
    assert payload["data"]["fallback_used"] is False
    assert FAKE_KEY not in json.dumps(payload)
    assert "api_key" not in json.dumps(payload)


def test_match_falls_back_locally_when_gemini_fails(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FailingGeminiProvider)
    client = api_client()
    _save_gemini_settings(client)

    response = client.post(
        "/api/v1/match/analyze",
        json={"resume_text": RESUME_TEXT, "job_text": JOB_TEXT},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["provider_used"] == "local"
    assert payload["data"]["analysis_mode"] == "fallback"
    assert payload["data"]["fallback_used"] is True
    assert payload["warnings"]


def test_match_toggle_false_keeps_analysis_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FakeGeminiProvider)
    client = api_client()
    _save_gemini_settings(client, allow_match=False)

    response = client.post(
        "/api/v1/match/analyze",
        json={"resume_text": RESUME_TEXT, "job_text": JOB_TEXT},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["provider_used"] == "local"
    assert payload["data"]["analysis_mode"] == "local"
    assert any("IA desativada para match" in item for item in payload["warnings"])


def test_area_toggles_keep_ats_tailor_and_github_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FakeGeminiProvider)
    captured: dict[str, object] = {}

    def fake_github_analysis(value: str, **kwargs):
        captured["provider"] = kwargs.get("provider")
        fallback_payload = ProjectAnalysisPayload(
            url="https://github.com/example/fictitious-api",
            owner="example",
            repo="fictitious-api",
            title="Fictitious API",
            page_type="github_repo",
            visible_text="FastAPI project with README and tests.",
            readme_text="# Fictitious API\nFastAPI project.",
            files_sampled=["README.md", "pyproject.toml", "tests/test_api.py"],
            languages=["Python"],
            topics=["api", "career"],
        )
        report = real_github_analysis("not-a-github-url", fallback_payload=fallback_payload)
        return report.model_copy(update={"provider_used": "local", "fallback_used": False})

    monkeypatch.setattr(
        "apps.api.services.analysis.analyze_github_repository", fake_github_analysis
    )
    client = api_client()
    _save_gemini_settings(client, allow_ats=False, allow_tailor=False, allow_github=False)

    ats = client.post(
        "/api/v1/ats/analyze",
        json={
            "resume_text": RESUME_TEXT,
            "job_text": JOB_TEXT,
            "job_keywords": ["Python", "Docker", "Kubernetes"],
        },
    )
    tailor = client.post(
        "/api/v1/resume/tailor",
        json={
            "target_role": "Desenvolvedor Backend Python",
            "job_text": JOB_TEXT,
            "evidence_text": RESUME_TEXT,
        },
    )
    github = client.post(
        "/api/v1/github/repo/analyze",
        json={
            "repo_url": "https://github.com/example/fictitious-api",
            "fallback_payload": {
                "url": "https://github.com/example/fictitious-api",
                "owner": "example",
                "repo": "fictitious-api",
                "title": "Fictitious API",
                "page_type": "github_repo",
                "visible_text": "FastAPI project with README and tests.",
                "readme_text": "# Fictitious API\nFastAPI project.",
                "files_sampled": ["README.md", "pyproject.toml", "tests/test_api.py"],
                "languages": ["Python"],
                "topics": ["api", "career"],
            },
        },
    )

    assert ats.status_code == 200
    assert ats.json()["data"]["provider_used"] == "local"
    assert not ats.json()["data"]["ai_insights"]
    assert any("IA desativada para ats" in item for item in ats.json()["warnings"])

    assert tailor.status_code == 200
    assert tailor.json()["data"]["provider_used"] == "local"
    assert not tailor.json()["data"]["ai_suggestions"]
    assert any("IA desativada para tailor" in item for item in tailor.json()["warnings"])

    assert github.status_code == 200
    assert captured["provider"] is None
    assert github.json()["data"]["provider_used"] == "local"
    assert any("IA desativada para github" in item for item in github.json()["warnings"])


def test_ats_and_tailor_use_gemini_prompts_without_leaking_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FakeGeminiProvider)
    client = api_client()
    _save_gemini_settings(client)

    ats = client.post(
        "/api/v1/ats/analyze",
        json={
            "resume_text": RESUME_TEXT,
            "job_text": JOB_TEXT,
            "job_keywords": ["Python", "Docker", "Kubernetes"],
        },
    )
    tailor = client.post(
        "/api/v1/resume/tailor",
        json={
            "target_role": "Desenvolvedor Backend Python",
            "job_text": JOB_TEXT,
            "evidence_text": RESUME_TEXT,
        },
    )

    assert ats.status_code == 200
    ats_payload = ats.json()
    assert ats_payload["data"]["provider_used"] == "gemini"
    assert ats_payload["data"]["analysis_mode"] == "ai"
    assert "Python aparece como evidencia direta." in ats_payload["data"]["ai_insights"]
    assert FAKE_KEY not in json.dumps(ats_payload)

    assert tailor.status_code == 200
    tailor_payload = tailor.json()
    assert tailor_payload["data"]["provider_used"] == "gemini"
    assert tailor_payload["data"]["analysis_mode"] == "ai"
    assert tailor_payload["data"]["ai_suggestions"]
    assert FAKE_KEY not in json.dumps(tailor_payload)


def test_github_analysis_receives_gemini_provider_when_enabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("apps.api.services.ai_settings.GeminiProvider", FakeGeminiProvider)
    captured: dict[str, str] = {}

    def fake_github_analysis(value: str, **kwargs):
        provider = kwargs.get("provider")
        captured["provider"] = getattr(provider, "name", "")
        fallback_payload = kwargs.get("fallback_payload") or ProjectAnalysisPayload(
            url="https://github.com/example/fictitious-api",
            owner="example",
            repo="fictitious-api",
            title="Fictitious API",
            page_type="github_repo",
            visible_text="FastAPI project with README and tests.",
            readme_text="# Fictitious API\nFastAPI project.",
            files_sampled=["README.md", "pyproject.toml", "tests/test_api.py"],
            languages=["Python"],
            topics=["api", "career"],
        )
        report = real_github_analysis("not-a-github-url", fallback_payload=fallback_payload)
        return report.model_copy(update={"provider_used": "gemini", "fallback_used": False})

    monkeypatch.setattr(
        "apps.api.services.analysis.analyze_github_repository", fake_github_analysis
    )
    client = api_client()
    _save_gemini_settings(client)

    response = client.post(
        "/api/v1/github/repo/analyze",
        json={
            "repo_url": "https://github.com/example/fictitious-api",
            "fallback_payload": {
                "url": "https://github.com/example/fictitious-api",
                "owner": "example",
                "repo": "fictitious-api",
                "title": "Fictitious API",
                "page_type": "github_repo",
                "visible_text": "FastAPI project with README and tests.",
                "readme_text": "# Fictitious API\nFastAPI project.",
                "files_sampled": ["README.md", "pyproject.toml", "tests/test_api.py"],
                "languages": ["Python"],
                "topics": ["api", "career"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert captured["provider"] == "gemini"
    assert payload["data"]["provider_used"] == "gemini"
    assert payload["data"]["analysis_mode"] == "ai"
    assert FAKE_KEY not in json.dumps(payload)
