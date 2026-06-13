"""Optional Gemini Structured Output provider."""

from __future__ import annotations

import importlib

from modules.ai.providers.base import AIProvider, ProviderUnavailableError
from modules.ai.setup import gemini_api_key, gemini_model
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class GeminiProvider(AIProvider):
    """Generate a Pydantic-validated analysis through the optional Gemini SDK."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = gemini_api_key(api_key)
        self.model = gemini_model(model)

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
    ) -> JobAnalysisSchema:
        """Call Gemini with response_schema when configuration is available."""
        if not self.api_key:
            raise ProviderUnavailableError("Gemini não configurado: informe GEMINI_API_KEY.")
        try:
            genai = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
        except ImportError as exc:
            raise ProviderUnavailableError("Instale requirements-ai.txt para usar Gemini.") from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=self._build_prompt(resume_text, job_text, preferences, job_details),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=self.structured_response_schema(),
                temperature=0,
            ),
        )
        if response.parsed:
            return JobAnalysisSchema.model_validate(response.parsed)
        return JobAnalysisSchema.model_validate_json(response.text)

    def ping(self) -> str:
        """Run a minimal Gemini call without structured output."""
        if not self.api_key:
            raise ProviderUnavailableError("Gemini não configurado: informe GEMINI_API_KEY.")
        try:
            genai = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
        except ImportError as exc:
            raise ProviderUnavailableError("Instale requirements-ai.txt para usar Gemini.") from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents="Responda apenas: ok",
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=8),
        )
        return (response.text or "").strip()

    @staticmethod
    def structured_response_schema() -> dict[str, object]:
        """Return the small JSON Schema subset accepted by Gemini structured output."""
        score = {"type": "integer", "minimum": 0, "maximum": 100}
        string_list = {"type": "array", "items": {"type": "string"}}
        return {
            "type": "object",
            "properties": {
                "match_score": score,
                "ats_score": score,
                "opportunity_fit_score": score,
                "risk_score": score,
                "recommendation": {
                    "type": "string",
                    "enum": ["apply", "apply_with_adjustments", "save_for_later", "ignore"],
                },
                "strengths": string_list,
                "gaps": string_list,
                "missing_keywords": string_list,
                "risk_flags": string_list,
                "tailored_summary": {"type": "string"},
                "recruiter_message": {"type": "string"},
            },
            "required": [
                "match_score",
                "ats_score",
                "opportunity_fit_score",
                "risk_score",
                "recommendation",
            ],
        }

    @staticmethod
    def _build_prompt(
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None,
        job_details: dict[str, object] | None,
    ) -> str:
        preference_json = (preferences or UserPreferences()).model_dump_json()
        return (
            "Analise o curriculo e a vaga. Nao invente fatos. Use apenas evidencias fornecidas. "
            "Retorne scores explicaveis entre 0 e 100 e uma recomendacao permitida.\n\n"
            f"PREFERENCIAS:\n{preference_json}\n\n"
            f"DADOS DA VAGA:\n{job_details or {}}\n\n"
            f"CURRICULO:\n{resume_text}\n\n"
            f"VAGA:\n{job_text}"
        )
