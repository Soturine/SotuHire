"""Optional OpenAI provider using backend-local secrets only."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from modules.ai.json_guard import validate_ai_json
from modules.ai.prompt_spec import PromptSpec
from modules.ai.providers.base import AIProvider, ProviderUnavailableError
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences

OpenAITransport = Callable[[dict[str, Any]], dict[str, Any]]

DEFAULT_OPENAI_MODEL = "gpt-5-mini"


class OpenAIProvider(AIProvider):
    """Generate validated JSON through OpenAI Responses API."""

    name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        transport: OpenAITransport | None = None,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.model = (model or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
        self.transport = transport

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
        memory_context: str = "",
    ) -> JobAnalysisSchema:
        """Return a validated job analysis, falling back only at caller level."""
        prompt = (
            "Analise o currículo e a vaga sem inventar fatos. Responda apenas JSON válido "
            "compatível com os campos de score e recomendação do SotuHire."
        )
        payload = {
            "resume_text": resume_text,
            "job_text": job_text,
            "preferences": (preferences or UserPreferences()).model_dump(mode="json"),
            "job_details": job_details or {},
            "memory_context": memory_context,
            "language": "pt-BR",
        }
        response = self._responses_request(prompt, json.dumps(payload, ensure_ascii=False))
        return validate_ai_json(_extract_response_text(response), JobAnalysisSchema).data

    def generate_structured(
        self,
        prompt: PromptSpec,
        payload: dict[str, object],
    ) -> BaseModel:
        """Run a Prompt Registry prompt and validate JSON locally."""
        response = self._responses_request(
            (
                f"{prompt.system_prompt}\n\n"
                "Responda somente JSON válido. Não use markdown. Não invente campos ausentes."
            ),
            prompt.render_user_prompt(payload),
            temperature=prompt.temperature,
        )
        return validate_ai_json(_extract_response_text(response), prompt.output_schema).data

    def ping(self) -> str:
        """Run a minimal OpenAI call for user-triggered connection tests."""
        response = self._responses_request("Responda apenas: ok", "ok", max_output_tokens=8)
        return _extract_response_text(response).strip()

    def _responses_request(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0,
        max_output_tokens: int = 4096,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise ProviderUnavailableError(
                "OpenAI não configurado: informe uma chave no backend local."
            )
        body = {
            "model": self.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }
        if self.transport is not None:
            return self.transport(body)
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ProviderUnavailableError("Falha ao chamar OpenAI pelo backend local.") from exc


def _extract_response_text(payload: dict[str, Any]) -> str:
    """Extract text from Responses API shapes without exposing raw secrets."""
    direct = payload.get("output_text")
    if isinstance(direct, str):
        return direct
    output = payload.get("output", [])
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for chunk in content:
                if isinstance(chunk, dict):
                    text = chunk.get("text")
                    if isinstance(text, str):
                        parts.append(text)
        if parts:
            return "\n".join(parts)
    choices = payload.get("choices", [])
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content", "") if isinstance(message, dict) else ""
        if isinstance(content, str):
            return content
    return ""
