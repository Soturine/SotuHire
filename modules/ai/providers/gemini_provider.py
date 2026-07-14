"""Optional Gemini Structured Output provider."""

from __future__ import annotations

import importlib
import time
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from modules.ai.json_guard import validate_ai_json
from modules.ai.prompt_spec import PromptSpec
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
        self.last_call_metadata: dict[str, Any] = {}

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
        memory_context: str = "",
    ) -> JobAnalysisSchema:
        """Call Gemini with response_schema when configuration is available."""
        if not self.api_key:
            raise ProviderUnavailableError("Gemini não configurado: informe GEMINI_API_KEY.")
        try:
            genai = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Instale com: pip install -r docs/requirements/requirements-ai.txt"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=self._build_prompt(
                resume_text,
                job_text,
                preferences,
                job_details,
                memory_context=memory_context,
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=self.structured_response_schema(),
                temperature=0,
            ),
        )
        if response.parsed:
            return JobAnalysisSchema.model_validate(response.parsed)
        return JobAnalysisSchema.model_validate_json(response.text)

    def generate_structured(
        self,
        prompt: PromptSpec,
        payload: dict[str, object],
    ) -> BaseModel:
        """Call Gemini for a prompt-specific structured extraction."""
        if not self.api_key:
            raise ProviderUnavailableError("Gemini não configurado: informe GEMINI_API_KEY.")
        try:
            genai = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Instale com: pip install -r docs/requirements/requirements-ai.txt"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        started_at = datetime.now(UTC)
        started_monotonic = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=(
                    f"{prompt.effective_system_prompt}\n\n"
                    "Return only JSON that matches the expected output schema.\n\n"
                    f"{prompt.render_user_prompt(payload)}"
                ),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=prompt.output_schema.model_json_schema(),
                    temperature=prompt.temperature,
                ),
            )
        except Exception as exc:
            self._record_call(started_at, started_monotonic, error_type=type(exc).__name__)
            raise
        self._record_call(started_at, started_monotonic, response=response)
        parsed = response.parsed if response.parsed else response.text
        if isinstance(parsed, prompt.output_schema):
            return parsed
        if isinstance(parsed, dict):
            return prompt.output_schema.model_validate(parsed)
        return validate_ai_json(parsed, prompt.output_schema).data

    def ping(self) -> str:
        """Run a minimal Gemini call without structured output."""
        if not self.api_key:
            raise ProviderUnavailableError("Gemini não configurado: informe GEMINI_API_KEY.")
        try:
            genai = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Instale com: pip install -r docs/requirements/requirements-ai.txt"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents="Responda apenas: ok",
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=8),
        )
        return (response.text or "ok").strip()

    def _record_call(
        self,
        started_at: datetime,
        started_monotonic: float,
        *,
        response: Any | None = None,
        error_type: str = "",
    ) -> None:
        usage = getattr(response, "usage_metadata", None)
        input_tokens = _integer(getattr(usage, "prompt_token_count", None))
        output_tokens = _integer(getattr(usage, "candidates_token_count", None))
        total_tokens = _integer(getattr(usage, "total_token_count", None))
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        self.last_call_metadata = {
            "started_at": started_at,
            "finished_at": datetime.now(UTC),
            "latency_ms": round((time.perf_counter() - started_monotonic) * 1000),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": None,
            "error_type": error_type,
        }

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
        memory_context: str = "",
    ) -> str:
        preference_json = (preferences or UserPreferences()).model_dump_json()
        relevant_memory = (
            f"\n\nCONTEXTO RELEVANTE DA MEMORIA AUTORIZADO PELO USUARIO:\n{memory_context}"
            if memory_context.strip()
            else ""
        )
        return (
            "Analise o curriculo e a vaga. Nao invente fatos. Use apenas evidencias fornecidas. "
            "Retorne scores explicaveis entre 0 e 100 e uma recomendacao permitida.\n\n"
            f"PREFERENCIAS:\n{preference_json}\n\n"
            f"DADOS DA VAGA:\n{job_details or {}}\n\n"
            f"CURRICULO:\n{resume_text}\n\n"
            f"VAGA:\n{job_text}"
            f"{relevant_memory}"
        )


def _integer(value: object) -> int | None:
    if not isinstance(value, str | int | float | bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
