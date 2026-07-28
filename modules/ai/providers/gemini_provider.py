"""Optional Gemini provider with native schemas, bounded retry and one-shot repair."""

from __future__ import annotations

import importlib
import random
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from modules.ai.prompt_spec import PromptSpec
from modules.ai.provider_errors import (
    ProviderCallError,
    ProviderError,
    ProviderErrorCategory,
    ProviderRetryPolicy,
    classify_gemini_error,
)
from modules.ai.providers.base import AIProvider, ProviderUnavailableError
from modules.ai.schema_repair import (
    SchemaRepairError,
    repair_instructions,
    validate_with_single_repair,
)
from modules.ai.setup import gemini_api_key, gemini_model
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.user_preferences import UserPreferences

GeminiTransport = Callable[[dict[str, Any]], Any]


class GeminiProvider(AIProvider):
    """Generate Pydantic-validated output through the optional Gemini SDK."""

    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        transport: GeminiTransport | None = None,
        retry_policy: ProviderRetryPolicy | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        random_value: Callable[[], float] = random.random,
    ) -> None:
        self.api_key = gemini_api_key(api_key)
        self.model = gemini_model(model)
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
        """Call Gemini with the compact analysis schema and controlled repair."""
        contents = self._build_prompt(
            resume_text,
            job_text,
            preferences,
            job_details,
            memory_context=memory_context,
        )
        config: dict[str, Any] = {
            "response_mime_type": "application/json",
            "response_json_schema": self.structured_response_schema(),
            "temperature": 0,
            "max_output_tokens": 8_192,
            "thinking_config": {"thinking_budget": 0},
        }
        return JobAnalysisSchema.model_validate(
            self._generate_and_validate(contents, config, JobAnalysisSchema)
        )

    def generate_structured(
        self,
        prompt: PromptSpec,
        payload: dict[str, object],
    ) -> BaseModel:
        """Use SDK-native Pydantic schema conversion, then validate and repair at most once."""
        contents = (
            f"{prompt.effective_system_prompt}\n\n"
            "Return only JSON that matches the expected output schema.\n\n"
            f"{prompt.render_user_prompt(payload)}"
        )
        config: dict[str, Any] = {
            "response_mime_type": "application/json",
            "response_json_schema": gemini_response_json_schema(prompt.output_schema),
            "temperature": prompt.temperature,
            "max_output_tokens": 8_192,
            "thinking_config": {"thinking_budget": 0},
        }
        return self._generate_and_validate(contents, config, prompt.output_schema)

    def ping(self) -> str:
        """Run a minimal Gemini call with the same diagnostic and retry contract."""
        response = self._generate_request(
            "Responda apenas: ok",
            {
                "temperature": 0,
                "max_output_tokens": 128,
                "thinking_config": {"thinking_budget": 0},
            },
        )
        text = _response_text(response).strip()
        if not text:
            raise self._provider_response_error(
                ProviderErrorCategory.EMPTY_RESPONSE,
                "Gemini retornou resposta vazia.",
                retryable=False,
            )
        return text

    def _generate_and_validate(
        self,
        contents: str,
        config: dict[str, Any],
        schema: type[BaseModel],
    ) -> BaseModel:
        response = self._generate_request(contents, config)
        original_metadata = dict(self.last_call_metadata)
        raw_output = _response_output(response)
        repair_metadata: dict[str, Any] = {}

        def repair(invalid_response: str, output_schema: dict[str, Any]) -> object:
            nonlocal repair_metadata
            system, user = repair_instructions(invalid_response, output_schema)
            repaired_response = self._generate_request(f"{system}\n\n{user}", config)
            repair_metadata = dict(self.last_call_metadata)
            return _response_output(repaired_response)

        try:
            result = validate_with_single_repair(raw_output, schema, repair)
        except ProviderCallError:
            self.last_call_metadata = _merge_metadata(
                original_metadata,
                dict(self.last_call_metadata),
                repaired=False,
                repair_attempted=True,
            )
            raise
        except SchemaRepairError as exc:
            self.last_call_metadata = _merge_metadata(
                original_metadata,
                repair_metadata,
                repaired=False,
                repair_attempted=True,
                repair_reason=exc.original_reason,
            )
            raise self._provider_response_error(
                ProviderErrorCategory.SCHEMA_INVALID,
                str(exc),
                retryable=False,
            ) from exc
        if result.repaired:
            self.last_call_metadata = _merge_metadata(
                original_metadata,
                repair_metadata,
                repaired=True,
                repair_attempted=True,
                repair_reason=result.repair_reason,
            )
        else:
            self.last_call_metadata = {
                **original_metadata,
                "repaired": False,
                "repair_attempted": False,
                "repair_reason": "",
            }
        return result.data

    def _generate_request(self, contents: str, config: dict[str, Any]) -> Any:
        started_at = datetime.now(UTC)
        started_monotonic = time.perf_counter()
        if not self.api_key:
            error = ProviderError(
                provider=self.name,
                model=self.model,
                error_code="missing_api_key",
                error_type="ProviderUnavailableError",
                category=ProviderErrorCategory.AUTHENTICATION,
                sanitized_message="Gemini não configurado no backend local.",
                max_attempts=self.retry_policy.max_attempts,
            )
            self._record_call(started_at, started_monotonic, provider_error=error)
            raise ProviderCallError(error)
        retry_history: list[dict[str, Any]] = []
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            error_response: Any | None = None
            try:
                response = self._execute_request(contents, config)
            except ProviderCallError as exc:
                error = exc.error.model_copy(
                    update={"attempt": attempt, "max_attempts": self.retry_policy.max_attempts}
                )
            except Exception as exc:
                error = classify_gemini_error(
                    exc,
                    model=self.model,
                    attempt=attempt,
                    max_attempts=self.retry_policy.max_attempts,
                )
            else:
                problem = _response_problem(
                    response,
                    provider=self.name,
                    model=self.model,
                    attempt=attempt,
                    max_attempts=self.retry_policy.max_attempts,
                )
                if problem is None:
                    self._record_call(
                        started_at,
                        started_monotonic,
                        response=response,
                        attempt=attempt,
                        retry_history=retry_history,
                    )
                    return response
                error = problem
                error_response = response
            retry_history.append(error.model_dump(mode="json"))
            if not error.retryable or attempt >= self.retry_policy.max_attempts:
                self._record_call(
                    started_at,
                    started_monotonic,
                    response=error_response,
                    provider_error=error,
                    attempt=attempt,
                    retry_history=retry_history,
                )
                raise ProviderCallError(error)
            self.sleeper(self.retry_policy.delay_seconds(error, random_value=self.random_value))
        raise RuntimeError("Gemini retry loop exited unexpectedly")

    def _execute_request(self, contents: str, config: dict[str, Any]) -> Any:
        payload = {"model": self.model, "contents": contents, "config": config}
        if self.transport is not None:
            return self.transport(payload)
        try:
            genai = importlib.import_module("google.genai")
            types = importlib.import_module("google.genai.types")
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Instale com: pip install -r docs/requirements/requirements-ai.txt"
            ) from exc
        client = genai.Client(api_key=self.api_key)
        sdk_config = types.GenerateContentConfig(**config)
        return client.models.generate_content(
            model=self.model,
            contents=contents,
            config=sdk_config,
        )

    def _provider_response_error(
        self,
        category: ProviderErrorCategory,
        message: str,
        *,
        retryable: bool,
    ) -> ProviderCallError:
        error = ProviderError(
            provider=self.name,
            model=self.model,
            error_code=category.value.casefold(),
            error_type="ProviderResponseError",
            category=category,
            retryable=retryable,
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
        response: Any | None = None,
        provider_error: ProviderError | None = None,
        attempt: int = 1,
        retry_history: list[dict[str, Any]] | None = None,
    ) -> None:
        usage = getattr(response, "usage_metadata", None)
        input_tokens = _integer(getattr(usage, "prompt_token_count", None))
        output_tokens = _integer(getattr(usage, "candidates_token_count", None))
        total_tokens = _integer(getattr(usage, "total_token_count", None))
        if total_tokens is None and (input_tokens is not None or output_tokens is not None):
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
        response_id = str(getattr(response, "response_id", "") or "")
        self.last_call_metadata = {
            "started_at": started_at,
            "finished_at": datetime.now(UTC),
            "latency_ms": round((time.perf_counter() - started_monotonic) * 1000),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": None,
            "error_type": provider_error.error_type if provider_error else "",
            "request_id": provider_error.request_id if provider_error else response_id,
            "response_id": response_id,
            "attempt": attempt,
            "max_attempts": self.retry_policy.max_attempts,
            "retries": max(0, attempt - 1),
            "retry_history": retry_history or [],
            "provider_error": (
                provider_error.model_dump(mode="json") if provider_error is not None else None
            ),
            "finish_reason": _finish_reason(response),
            "safety_status": _safety_status(response),
            "raw_shape": _response_shape(response),
            "repaired": False,
            "repair_attempted": False,
            "repair_reason": "",
        }

    @staticmethod
    def structured_response_schema() -> dict[str, object]:
        """Return the small JSON Schema subset accepted by Gemini analysis."""
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


def _response_output(response: Any) -> object:
    parsed = getattr(response, "parsed", None)
    return parsed if parsed is not None else _response_text(response)


def _response_text(response: Any) -> str:
    value = getattr(response, "text", "")
    return value if isinstance(value, str) else ""


def _response_problem(
    response: Any,
    *,
    provider: str,
    model: str,
    attempt: int,
    max_attempts: int,
) -> ProviderError | None:
    finish = _finish_reason(response).upper()
    if any(value in finish for value in ("SAFETY", "PROHIBITED", "BLOCKLIST")):
        category, message, retryable = (
            ProviderErrorCategory.SAFETY_BLOCK,
            f"Resposta bloqueada por segurança ({finish}).",
            False,
        )
    elif "MAX_TOKENS" in finish:
        category, message, retryable = (
            ProviderErrorCategory.TRUNCATED_RESPONSE,
            "Resposta truncada pelo limite de output.",
            True,
        )
    elif getattr(response, "parsed", None) is None and not _response_text(response).strip():
        category, message, retryable = (
            ProviderErrorCategory.EMPTY_RESPONSE,
            "Provider retornou resposta vazia.",
            True,
        )
    else:
        return None
    return ProviderError(
        provider=provider,
        model=model,
        error_code=category.value.casefold(),
        error_type="ProviderResponseError",
        category=category,
        retryable=retryable,
        request_id=str(getattr(response, "response_id", "") or ""),
        sanitized_message=message,
        attempt=attempt,
        max_attempts=max_attempts,
    )


def _finish_reason(response: Any) -> str:
    candidates = getattr(response, "candidates", None)
    if isinstance(candidates, list) and candidates:
        value = getattr(candidates[0], "finish_reason", "")
        if value:
            return str(getattr(value, "name", value))
    return ""


def _safety_status(response: Any) -> str:
    candidates = getattr(response, "candidates", None)
    if not isinstance(candidates, list) or not candidates:
        return ""
    ratings = getattr(candidates[0], "safety_ratings", None)
    if not isinstance(ratings, list):
        return ""
    blocked = [
        str(getattr(item, "category", "unknown"))
        for item in ratings
        if bool(getattr(item, "blocked", False))
    ]
    return ",".join(blocked) if blocked else "clear"


def _response_shape(response: Any) -> dict[str, Any]:
    candidates = getattr(response, "candidates", None)
    return {
        "response_type": type(response).__name__,
        "parsed_type": type(getattr(response, "parsed", None)).__name__,
        "text_present": bool(_response_text(response).strip()),
        "candidate_count": len(candidates) if isinstance(candidates, list) else 0,
    }


def _merge_metadata(
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
                    "finish_reason",
                    "safety_status",
                    "raw_shape",
                    "error_type",
                    "provider_error",
                }
            },
        }
    )
    return merged


def _integer(value: object) -> int | None:
    if not isinstance(value, str | int | float | bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def gemini_response_json_schema(schema: type[BaseModel]) -> dict[str, Any]:
    """Return standard JSON Schema without keywords rejected by Gemini generation config."""
    unsupported = {
        "$schema",
        "additionalProperties",
        "default",
        "deprecated",
        "examples",
        "readOnly",
        "title",
        "writeOnly",
    }

    def normalize(value: object) -> object:
        if isinstance(value, dict):
            normalized: dict[str, object] = {}
            for key, nested in value.items():
                if key in unsupported:
                    continue
                if key == "const":
                    normalized["enum"] = [normalize(nested)]
                    continue
                normalized[key] = normalize(nested)
            return normalized
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    result = normalize(schema.model_json_schema())
    return result if isinstance(result, dict) else {}
