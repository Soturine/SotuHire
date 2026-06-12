"""Optional Gemini Structured Output provider."""

from __future__ import annotations

import os

from modules.ai.providers.base import AIProvider, ProviderUnavailableError
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences


class GeminiProvider(AIProvider):
    """Generate a Pydantic-validated analysis through the optional Gemini SDK."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
    ) -> JobAnalysisSchema:
        """Call Gemini with response_schema when configuration is available."""
        if not self.api_key:
            raise ProviderUnavailableError("GEMINI_API_KEY nao configurada.")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Instale requirements-ai.txt para habilitar o Gemini."
            ) from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=self._build_prompt(resume_text, job_text, preferences, job_details),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobAnalysisSchema,
                temperature=0,
            ),
        )
        if response.parsed:
            return JobAnalysisSchema.model_validate(response.parsed)
        return JobAnalysisSchema.model_validate_json(response.text)

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
