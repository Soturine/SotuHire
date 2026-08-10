"""Explicit, SSRF-safe interoperability with user-selected local AI servers."""

from __future__ import annotations

import http.client
import ipaddress
import json
import time
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, ConfigDict, Field

from modules.ai.exceptions import ProviderUnavailableError
from modules.ai.prompt_spec import PromptSpec
from modules.ai.providers.base import AIProvider
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences
from modules.scraping.http_safety import request_public_url, validate_public_url

LocalAiProviderId = Literal["ollama", "lm_studio", "openai_compatible"]
DEFAULT_LOCAL_ENDPOINTS: dict[LocalAiProviderId, str] = {
    "ollama": "http://127.0.0.1:11434/v1",
    "lm_studio": "http://127.0.0.1:1234/v1",
    "openai_compatible": "http://127.0.0.1:8000/v1",
}


class LocalAiEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: LocalAiProviderId
    base_url: str
    hostname: str
    port: int
    remote: bool
    advanced_remote_opt_in: bool = False


class LocalAiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    owned_by: str = "local"


class LocalAiHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: LocalAiProviderId
    endpoint: str
    status: Literal["ready", "offline", "error"]
    latency_ms: int | None = None
    models: list[LocalAiModel] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    checked_at: str
    message: str = ""


def validate_local_ai_endpoint(
    provider: LocalAiProviderId,
    endpoint: str,
    *,
    advanced_remote_opt_in: bool = False,
) -> LocalAiEndpoint:
    """Accept loopback by default; custom remote requires explicit HTTPS and public DNS/IP."""
    raw = (endpoint or DEFAULT_LOCAL_ENDPOINTS[provider]).strip()
    parsed = urlparse(raw)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Endpoint de IA local deve usar HTTP ou HTTPS.")
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Endpoint de IA não pode conter credenciais, query ou fragmento.")
    try:
        port = parsed.port or (443 if parsed.scheme.casefold() == "https" else 80)
    except ValueError as exc:
        raise ValueError("Porta do endpoint de IA inválida.") from exc
    hostname = parsed.hostname.rstrip(".").casefold()
    loopback = hostname == "localhost"
    if not loopback:
        try:
            loopback = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            loopback = False
    if not loopback:
        if not advanced_remote_opt_in:
            raise ValueError("Endpoint remoto exige opt-in avançado explícito.")
        if parsed.scheme.casefold() != "https":
            raise ValueError("Endpoint remoto customizado exige HTTPS.")
        validate_public_url(raw, resolve=True)
    path = parsed.path.rstrip("/")
    if not path:
        path = "/v1"
    normalized = urlunparse((parsed.scheme.casefold(), parsed.netloc, path, "", "", ""))
    return LocalAiEndpoint(
        provider=provider,
        base_url=normalized,
        hostname=hostname,
        port=port,
        remote=not loopback,
        advanced_remote_opt_in=advanced_remote_opt_in,
    )


def local_ai_health(
    provider: LocalAiProviderId,
    endpoint: str = "",
    *,
    advanced_remote_opt_in: bool = False,
    api_key: str = "",
    timeout: float = 5,
) -> LocalAiHealth:
    """Check only the explicit endpoint; never scan ports or the local network."""
    checked_at = datetime.now(UTC).isoformat()
    try:
        config = validate_local_ai_endpoint(
            provider,
            endpoint,
            advanced_remote_opt_in=advanced_remote_opt_in,
        )
        started = time.perf_counter()
        payload = _request_json(config, "/models", api_key=api_key, timeout=timeout)
        latency = round((time.perf_counter() - started) * 1000)
        entries = payload.get("data", []) if isinstance(payload, dict) else []
        models = [
            LocalAiModel(id=str(item.get("id", "")), owned_by=str(item.get("owned_by", "local")))
            for item in entries
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ]
        return LocalAiHealth(
            provider=provider,
            endpoint=config.base_url,
            status="ready",
            latency_ms=latency,
            models=models,
            capabilities=["openai_compatible", "model_listing", "json", "structured_output"],
            checked_at=checked_at,
            message="Endpoint respondeu à listagem explícita de modelos.",
        )
    except (OSError, ValueError, ProviderUnavailableError) as exc:
        return LocalAiHealth(
            provider=provider,
            endpoint=endpoint or DEFAULT_LOCAL_ENDPOINTS[provider],
            status="offline" if isinstance(exc, OSError) else "error",
            checked_at=checked_at,
            message=f"Endpoint indisponível ou inválido ({type(exc).__name__}).",
        )


class OpenAICompatibleLocalProvider(AIProvider):
    """Validated structured-output adapter for Ollama, LM Studio and compatible servers."""

    def __init__(
        self,
        provider: LocalAiProviderId,
        *,
        endpoint: str = "",
        model: str,
        api_key: str = "",
        advanced_remote_opt_in: bool = False,
    ) -> None:
        self.endpoint = validate_local_ai_endpoint(
            provider,
            endpoint,
            advanced_remote_opt_in=advanced_remote_opt_in,
        )
        self.name = provider
        self.model = model.strip()
        self.api_key = api_key.strip()
        self.last_call_metadata: dict[str, Any] = {}
        if not self.model:
            raise ValueError("Selecione explicitamente um modelo local.")

    def analyze(
        self,
        resume_text: str,
        job_text: str,
        preferences: UserPreferences | None = None,
        job_details: dict[str, object] | None = None,
        memory_context: str = "",
    ) -> JobAnalysisSchema:
        content = self._complete(
            "Analise sem inventar fatos e responda somente JSON válido.",
            json.dumps(
                {
                    "resume_text": resume_text,
                    "job_text": job_text,
                    "preferences": (preferences or UserPreferences()).model_dump(mode="json"),
                    "job_details": job_details or {},
                    "memory_context": memory_context,
                },
                ensure_ascii=False,
            ),
            JobAnalysisSchema,
            "job_analysis",
        )
        return JobAnalysisSchema.model_validate_json(content)

    def generate_structured(self, prompt: PromptSpec, payload: dict[str, object]) -> BaseModel:
        content = self._complete(
            prompt.effective_system_prompt,
            prompt.render_user_prompt(payload),
            prompt.output_schema,
            prompt.prompt_id,
        )
        return prompt.output_schema.model_validate_json(content)

    def _complete(
        self,
        system: str,
        user: str,
        schema: type[BaseModel],
        schema_name: str,
    ) -> str:
        started = time.perf_counter()
        response = _request_json(
            self.endpoint,
            "/chat/completions",
            api_key=self.api_key,
            timeout=30,
            method="POST",
            payload={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name.replace("-", "_")[:64],
                        "strict": True,
                        "schema": schema.model_json_schema(),
                    },
                },
            },
        )
        try:
            content = str(response["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailableError(
                "Provider local retornou contrato incompatível."
            ) from exc
        self.last_call_metadata = {
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "provider": self.name,
            "model": self.model,
            "remote": self.endpoint.remote,
        }
        return content


def _request_json(
    endpoint: LocalAiEndpoint,
    path: str,
    *,
    api_key: str,
    timeout: float,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    url = f"{endpoint.base_url}{path}"
    if endpoint.remote:
        response = request_public_url(
            url,
            headers=headers,
            timeout=timeout,
            max_bytes=2_000_000,
            method=method,
            body=body,
        )
        status = response.status
        content = response.body
    else:
        address = "127.0.0.1" if endpoint.hostname == "localhost" else endpoint.hostname
        connection_class = (
            http.client.HTTPSConnection
            if urlparse(endpoint.base_url).scheme == "https"
            else http.client.HTTPConnection
        )
        connection = connection_class(address, endpoint.port, timeout=timeout)
        try:
            parsed = urlparse(url)
            request_path = parsed.path or "/"
            connection.request(method, request_path, body=body, headers=headers)
            raw = connection.getresponse()
            status = raw.status
            content = raw.read(2_000_001)
        finally:
            connection.close()
    if len(content) > 2_000_000:
        raise ProviderUnavailableError("Resposta do provider local excedeu o limite seguro.")
    if status >= 400:
        raise ProviderUnavailableError(f"Provider local respondeu HTTP {status}.")
    try:
        parsed_payload = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProviderUnavailableError("Provider local não retornou JSON válido.") from exc
    if not isinstance(parsed_payload, dict):
        raise ProviderUnavailableError("Provider local retornou payload incompatível.")
    return parsed_payload


__all__ = [
    "DEFAULT_LOCAL_ENDPOINTS",
    "LocalAiEndpoint",
    "LocalAiHealth",
    "LocalAiModel",
    "LocalAiProviderId",
    "OpenAICompatibleLocalProvider",
    "local_ai_health",
    "validate_local_ai_endpoint",
]
