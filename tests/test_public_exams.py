from __future__ import annotations

import json
from pathlib import Path

from modules.core.text_utils import normalize_text
from modules.public_exams import PublicExamImportInput, parse_public_exam_notice
from modules.public_exams.study_plan import build_study_plan
from tests.api_test_helpers import api_client

EDITAL_TEXT = """
Edital n 01/2026 - Concurso Publico Prefeitura Exemplo
Orgao: Prefeitura Municipal de Exemplo
Banca organizadora: Instituto Exemplo
Cargo: Engenheiro Civil
Vagas: 2
Local de prova: Sao Jose dos Campos
Salario: R$ 6.200,00
Taxa de inscricao: R$ 120,00
Carga horaria: 40h semanais
Inscricoes: 01/08/2026 a 20/08/2026
Pagamento da taxa: ate 21/08/2026
Prova objetiva: 13/09/2026
Resultado: 30/09/2026
Requisitos: graduacao concluida em Engenharia Civil e registro ativo no CREA.
Documentos: documento de identidade, CPF, diploma, registro profissional e quitacao eleitoral.
Etapas: prova objetiva e prova de titulos.
Conteudo programatico
Lingua Portuguesa: interpretacao de texto, concordancia, pontuacao.
Conhecimentos Especificos: licitacoes, obras publicas, fiscalizacao de contratos.
"""


def test_public_exam_parser_extracts_core_edital_fields() -> None:
    result = parse_public_exam_notice(PublicExamImportInput(text=EDITAL_TEXT, use_ai=False))

    notice = result.notice
    assert notice.organization == "Prefeitura Municipal de Exemplo"
    assert notice.exam_board == "Instituto Exemplo"
    assert notice.notice_number == "01/2026"
    assert notice.registration_fee == "R$ 120,00"
    assert notice.timeline.registration_start == "01/08/2026"
    assert notice.timeline.registration_end == "20/08/2026"
    assert notice.timeline.payment_deadline == "21/08/2026"
    assert notice.timeline.exam_date == "13/09/2026"
    assert notice.roles[0].title == "Engenheiro Civil"
    assert notice.roles[0].salary == "R$ 6.200,00"
    assert notice.roles[0].required_registry == "CREA"
    assert any(req.kind == "professional_registry" for req in result.requirements)
    assert any(
        subject.name == "Lingua Portuguesa" or "Portuguesa" in subject.name
        for subject in result.subjects
    )
    assert result.needs_user_review is True
    assert any("edital oficial" in warning.lower() for warning in result.warnings)


def test_public_exam_parser_warns_on_short_or_incomplete_text() -> None:
    result = parse_public_exam_notice(PublicExamImportInput(text="Cargo: Analista"))

    assert result.needs_user_review is True
    assert any("Texto curto" in warning for warning in result.warnings)
    assert any("data clara de prova" in warning for warning in result.warnings)
    assert any("requisitos claros" in warning for warning in result.warnings)


def test_public_exam_import_does_not_save_until_confirm(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    imported = client.post(
        "/api/v1/public-exams/import",
        json={"text": EDITAL_TEXT, "use_ai": False},
    )
    assert imported.status_code == 200
    draft = imported.json()["data"]
    assert draft["analysis_mode"] == "local"
    assert draft["needs_user_review"] is True

    listed_before = client.get("/api/v1/public-exams")
    assert listed_before.status_code == 200
    assert listed_before.json()["data"]["notices"] == []

    notice = draft["notice"]
    confirmed = client.post(
        f"/api/v1/public-exams/{notice['notice_id']}/confirm",
        json={"notice": notice},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["notice"]["status"] == "confirmed"
    assert "autom" not in normalize_text(confirmed.json()["data"]["message"])

    listed_after = client.get("/api/v1/public-exams")
    assert len(listed_after.json()["data"]["notices"]) == 1


def test_public_exam_ai_draft_uses_provider_but_remains_review_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class FakeProvider:
        name = "gemini"

        def generate_structured(self, prompt, payload):  # noqa: ANN001
            assert prompt.prompt_id == "public_exam_notice_extractor_v1"
            serialized = json.dumps(payload).lower()
            assert "api_key" not in serialized
            return payload["local_parser_draft"]

    monkeypatch.setattr(
        "apps.api.services.public_exams.get_ai_runtime",
        lambda feature: type(
            "Runtime",
            (),
            {
                "provider": FakeProvider(),
                "provider_name": "gemini",
                "requested_provider": "gemini",
                "use_ai": True,
                "warnings": [],
            },
        )(),
    )
    client = api_client()

    response = client.post(
        "/api/v1/public-exams/import",
        json={"text": EDITAL_TEXT, "use_ai": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_mode"] == "ai"
    assert data["provider_used"] == "gemini"
    assert data["needs_user_review"] is True


def test_public_exam_ai_failure_falls_back_to_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class BadProvider:
        name = "gemini"

        def generate_structured(self, prompt, payload):  # noqa: ANN001, ARG002
            return {"notice": {"title": ""}, "analysis_mode": "impossible"}

    monkeypatch.setattr(
        "apps.api.services.public_exams.get_ai_runtime",
        lambda feature: type(
            "Runtime",
            (),
            {
                "provider": BadProvider(),
                "provider_name": "gemini",
                "requested_provider": "gemini",
                "use_ai": True,
                "warnings": [],
            },
        )(),
    )
    client = api_client()

    response = client.post(
        "/api/v1/public-exams/import",
        json={"text": EDITAL_TEXT, "use_ai": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analysis_mode"] == "fallback"
    assert data["provider_used"] == "local"
    assert data["roles"][0]["title"] == "Engenheiro Civil"


def test_public_exam_import_uses_selected_openai_model_without_saving(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    captured: dict[str, str] = {}

    class FakeOpenAIProvider:
        name = "openai"

        def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
            captured["api_key"] = api_key or ""
            captured["model"] = model or ""
            self.model = model or ""

        def generate_structured(self, prompt, payload):  # noqa: ANN001
            assert prompt.prompt_id == "public_exam_notice_extractor_v1"
            return payload["local_parser_draft"]

    monkeypatch.setattr("apps.api.services.ai_settings.OpenAIProvider", FakeOpenAIProvider)
    client = api_client()
    client.post(
        "/api/v1/settings/ai",
        json={
            "provider": "openai",
            "model": "gpt-public-exam-test",
            "api_key": "openai-fake-secret",
            "use_ai": True,
            "allow_public_exams": True,
        },
    )

    response = client.post(
        "/api/v1/public-exams/import",
        json={"text": EDITAL_TEXT, "use_ai": True},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["provider_used"] == "openai"
    assert data["requested_provider"] == "openai"
    assert data["analysis_mode"] == "ai"
    assert data["needs_user_review"] is True
    assert captured["model"] == "gpt-public-exam-test"
    assert client.get("/api/v1/public-exams").json()["data"]["notices"] == []
    assert "openai-fake-secret" not in json.dumps(data)


def test_public_exam_analyze_is_conservative_with_profile_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()

    client.put(
        "/api/v1/profile",
        json={
            "target_roles": ["Engenheiro Civil"],
            "primary_domains": ["Engenharia"],
            "preferred_locations": ["Sao Jose dos Campos"],
        },
    )
    client.post(
        "/api/v1/profile/items",
        json={
            "type": "education",
            "title": "Graduacao em Engenharia Civil em andamento",
            "description": "Curso em andamento, sem diploma concluido.",
            "status": "in_progress",
            "domain": "Engenharia",
            "source": "manual",
            "evidence": "Usuario informou graduacao em andamento.",
        },
    )
    client.post(
        "/api/v1/profile/items",
        json={
            "type": "research_project",
            "title": "Projeto de pesquisa em obras publicas",
            "description": "Evidencia academica/Lattes confirmada pelo usuario.",
            "domain": "Pesquisa academica",
            "source": "curriculum_lattes",
            "evidence": "Projeto academico confirmado.",
        },
    )
    draft = client.post(
        "/api/v1/public-exams/import",
        json={"text": EDITAL_TEXT, "use_ai": False},
    ).json()["data"]
    notice = draft["notice"]
    client.post(f"/api/v1/public-exams/{notice['notice_id']}/confirm", json={"notice": notice})

    analyzed = client.post(f"/api/v1/public-exams/{notice['notice_id']}/analyze", json={})

    assert analyzed.status_code == 200
    data = analyzed.json()["data"]
    fit = data["fit_score"]
    missing = json.dumps(fit["missing_requirements"]).lower()
    assert fit["recommendation"] in {"review_requirements", "risky", "not_recommended"}
    assert "crea" in missing
    assert "andamento" not in json.dumps(fit["matched_requirements"]).lower()
    assert data["context_summary"]
    assert fit["matched_requirements"] or fit["uncertain_requirements"] or data["checklist"]
    assert "api_key" not in json.dumps(data).lower()


def test_public_exam_study_plan_with_and_without_exam_date() -> None:
    draft = parse_public_exam_notice(PublicExamImportInput(text=EDITAL_TEXT))

    plan = build_study_plan(draft.notice, draft.roles[0], weekly_hours=10)
    assert plan.days_until_exam is not None
    assert plan.weekly_hours == 10
    assert plan.priority_topics
    assert plan.schedule_blocks

    no_date_notice = draft.notice.model_copy(
        update={"timeline": draft.notice.timeline.model_copy(update={"exam_date": ""})}
    )
    no_date_plan = build_study_plan(no_date_notice, draft.roles[0], weekly_hours=6)
    assert no_date_plan.days_until_exam is None
    assert any("sem calendario" in normalize_text(warning) for warning in no_date_plan.warnings)


def test_public_exam_security_docs_and_authenticated_browser_guard() -> None:
    assert not Path("docs/ethics/allowed-vs-not-allowed.md").exists()
    assert Path("modules/scraping/browser_session.py").exists()
    assert Path("modules/scraping/connectors/authenticated_browser.py").exists()
