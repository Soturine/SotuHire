"""Optional OpenAI provider using backend-local secrets only."""

from __future__ import annotations

import json
import random
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from modules.ai.json_guard import validate_ai_json
from modules.ai.prompt_spec import PromptSpec
from modules.ai.provider_errors import (
    ProviderCallError,
    ProviderError,
    ProviderErrorCategory,
    ProviderRetryPolicy,
    classify_openai_error,
)
from modules.ai.providers.base import AIProvider
from modules.ai.schema_repair import (
    SchemaRepairError,
    repair_instructions,
    validate_with_single_repair,
)
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
        retry_policy: ProviderRetryPolicy | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        random_value: Callable[[], float] = random.random,
    ) -> None:
        self.api_key = (api_key or "").strip()
        self.model = (model or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
        self.transport = transport
        self.retry_policy = retry_policy or ProviderRetryPolicy()
        self.sleeper = sleeper
        self.random_value = random_value
        self.last_call_metadata: dict[str, Any] = {}

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
                f"{prompt.effective_system_prompt}\n\n"
                "Responda somente JSON válido. Não use markdown. Não invente campos ausentes."
            ),
            prompt.render_user_prompt(payload),
            temperature=prompt.temperature,
            response_schema=prompt.output_schema,
            schema_name=prompt.prompt_id,
        )
        text = _extract_response_text(response)
        if not text.strip():
            raise self._response_error(
                ProviderErrorCategory.EMPTY_RESPONSE,
                "OpenAI retornou resposta vazia.",
            )
        original_metadata = dict(self.last_call_metadata)
        repair_metadata: dict[str, Any] = {}

        def repair(invalid_response: str, output_schema: dict[str, Any]) -> object:
            nonlocal repair_metadata
            system, user = repair_instructions(invalid_response, output_schema)
            repaired_response = self._responses_request(
                system,
                user,
                temperature=0,
                response_schema=prompt.output_schema,
                schema_name=f"{prompt.prompt_id}_repair",
            )
            repair_metadata = dict(self.last_call_metadata)
            repaired_text = _extract_response_text(repaired_response)
            if not repaired_text.strip():
                raise self._response_error(
                    ProviderErrorCategory.EMPTY_RESPONSE,
                    "OpenAI retornou reparo vazio.",
                )
            return repaired_text

        try:
            result = validate_with_single_repair(text, prompt.output_schema, repair)
        except ProviderCallError:
            self.last_call_metadata = _merge_repair_metadata(
                original_metadata,
                dict(self.last_call_metadata),
                repaired=False,
                repair_attempted=True,
            )
            raise
        except SchemaRepairError as exc:
            self.last_call_metadata = _merge_repair_metadata(
                original_metadata,
                repair_metadata,
                repaired=False,
                repair_attempted=True,
                repair_reason=exc.original_reason,
            )
            raise self._response_error(
                ProviderErrorCategory.SCHEMA_INVALID,
                str(exc),
            ) from exc
        self.last_call_metadata = _merge_repair_metadata(
            original_metadata,
            repair_metadata,
            repaired=result.repaired,
            repair_attempted=result.repaired,
            repair_reason=result.repair_reason,
        )
        return result.data

    def ping(self) -> str:
        """Run a minimal OpenAI call for user-triggered connection tests."""
        response = self._responses_request("Responda apenas: ok", "ok", max_output_tokens=32)
        return _extract_response_text(response).strip()

    def _responses_request(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0,
        max_output_tokens: int = 4096,
        response_schema: type[BaseModel] | None = None,
        schema_name: str = "response",
    ) -> dict[str, Any]:
        started_at = datetime.now(UTC)
        started_monotonic = time.perf_counter()
        if not self.api_key:
            error = ProviderError(
                provider=self.name,
                model=self.model,
                error_code="missing_api_key",
                error_type="ProviderUnavailableError",
                category=ProviderErrorCategory.AUTHENTICATION,
                sanitized_message="OpenAI não configurado no backend local.",
                max_attempts=self.retry_policy.max_attempts,
            )
            self._record_call(started_at, started_monotonic, provider_error=error)
            raise ProviderCallError(error)
        body: dict[str, Any] = {
            "model": self.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_output_tokens": max_output_tokens,
        }
        if not self.model.lower().startswith(("gpt-5", "o1", "o3", "o4")):
            body["temperature"] = temperature
        if response_schema is not None:
            body["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": _schema_name(schema_name),
                    "schema": response_schema.model_json_schema(),
                    "strict": False,
                }
            }
        retry_history: list[dict[str, Any]] = []
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                payload = self._execute_request(body)
            except ProviderCallError as exc:
                error = exc.error.model_copy(
                    update={"attempt": attempt, "max_attempts": self.retry_policy.max_attempts}
                )
            except urllib.error.HTTPError as exc:
                error_body = _read_http_error(exc)
                error = classify_openai_error(
                    model=self.model,
                    status_code=exc.code,
                    headers=exc.headers,
                    body=error_body,
                    exception=exc,
                    attempt=attempt,
                    max_attempts=self.retry_policy.max_attempts,
                )
            except urllib.error.URLError as exc:
                error = classify_openai_error(
                    model=self.model,
                    status_code=getattr(exc, "code", None),
                    headers=getattr(exc, "headers", None),
                    exception=exc,
                    attempt=attempt,
                    max_attempts=self.retry_policy.max_attempts,
                )
            except (TimeoutError, OSError) as exc:
                error = classify_openai_error(
                    model=self.model,
                    status_code=None,
                    exception=exc,
                    attempt=attempt,
                    max_attempts=self.retry_policy.max_attempts,
                )
            except Exception as exc:
                self._record_call(
                    started_at,
                    started_monotonic,
                    error_type=type(exc).__name__,
                    attempt=attempt,
                    retry_history=retry_history,
                )
                raise
            else:
                self._record_call(
                    started_at,
                    started_monotonic,
                    payload=payload,
                    attempt=attempt,
                    retry_history=retry_history,
                )
                if str(payload.get("status", "")).casefold() == "incomplete":
                    reason = payload.get("incomplete_details", {})
                    raise self._response_error(
                        ProviderErrorCategory.TRUNCATED_RESPONSE,
                        f"Resposta incompleta: {reason}",
                    )
                return payload
            retry_history.append(error.model_dump(mode="json"))
            if not error.retryable or attempt >= self.retry_policy.max_attempts:
                self._record_call(
                    started_at,
                    started_monotonic,
                    provider_error=error,
                    attempt=attempt,
                    retry_history=retry_history,
                )
                raise ProviderCallError(error)
            self.sleeper(self.retry_policy.delay_seconds(error, random_value=self.random_value))
        raise RuntimeError("OpenAI retry loop exited unexpectedly")

    def _execute_request(self, body: dict[str, Any]) -> dict[str, Any]:
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
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _response_error(self, category: ProviderErrorCategory, message: str) -> ProviderCallError:
        error = ProviderError(
            provider=self.name,
            model=self.model,
            error_code=category.value.casefold(),
            error_type="ProviderResponseError",
            category=category,
            sanitized_message=message,
            attempt=int(self.last_call_metadata.get("attempt") or 1),
            max_attempts=self.retry_policy.max_attempts,
        )
        self.last_call_metadata.update(
            {
                "error_type": error.error_type,
                "provider_error": error.model_dump(mode="json"),
            }
        )
        return ProviderCallError(error)

    def _record_call(
        self,
        started_at: datetime,
        started_monotonic: float,
        *,
        payload: dict[str, Any] | None = None,
        error_type: str = "",
        provider_error: ProviderError | None = None,
        attempt: int = 1,
        retry_history: list[dict[str, Any]] | None = None,
    ) -> None:
        usage = payload.get("usage", {}) if isinstance(payload, dict) else {}
        input_tokens = _integer(usage.get("input_tokens")) if isinstance(usage, dict) else None
        output_tokens = _integer(usage.get("output_tokens")) if isinstance(usage, dict) else None
        total_tokens = _integer(usage.get("total_tokens")) if isinstance(usage, dict) else None
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        response_id = str(payload.get("id", "")) if isinstance(payload, dict) else ""
        self.last_call_metadata = {
            "started_at": started_at,
            "finished_at": datetime.now(UTC),
            "latency_ms": round((time.perf_counter() - started_monotonic) * 1000),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": None,
            "error_type": provider_error.error_type if provider_error else error_type,
            "request_id": provider_error.request_id if provider_error else response_id,
            "response_id": response_id,
            "attempt": attempt,
            "max_attempts": self.retry_policy.max_attempts,
            "retries": max(0, attempt - 1),
            "retry_history": retry_history or [],
            "provider_error": (
                provider_error.model_dump(mode="json") if provider_error is not None else None
            ),
        }


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


def _integer(value: object) -> int | None:
    if not isinstance(value, str | int | float | bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _read_http_error(error: urllib.error.HTTPError) -> bytes:
    try:
        return error.read(64_000)
    except (OSError, ValueError):
        return b""


def _schema_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return (cleaned or "sotuhire_response")[:64]


def _merge_repair_metadata(
    original: dict[str, Any],
    repair: dict[str, Any],
    *,
    repaired: bool,
    repair_attempted: bool,
    repair_reason: str = "",
) -> dict[str, Any]:
    merged = dict(original)
    for field in ("latency_ms", "input_tokens", "output_tokens", "total_tokens", "retries"):
        values = [value.get(field) for value in (original, repair)]
        numeric = [int(value) for value in values if isinstance(value, int | float)]
        merged[field] = sum(numeric) if numeric else None
    if repair:
        merged["finished_at"] = repair.get("finished_at", original.get("finished_at"))
    merged.update(
        {
            "repaired": repaired,
            "repair_attempted": repair_attempted,
            "repair_reason": repair_reason,
            "repair_call_metadata": {
                key: value
                for key, value in repair.items()
                if key
                in {
                    "latency_ms",
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "request_id",
                    "response_id",
                    "error_type",
                    "provider_error",
                }
            },
        }
    )
    return merged
