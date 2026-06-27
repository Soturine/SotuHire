"""Secure local storage and diagnostics for AI provider settings."""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from modules.ai import setup as ai_setup
from modules.ai.providers import AIProvider, GeminiProvider, MockProvider
from pydantic import ValidationError

from apps.api.schemas.settings import (
    AiProvider,
    AiSettingsResponse,
    AiSettingsTestRequest,
    AiSettingsTestResponse,
    AiSettingsUpdateRequest,
)

AI_TEST_TIMEOUT_SECONDS = 8
SETTINGS_RELATIVE_PATH = Path("settings") / "ai-settings.json"
SECRETS_RELATIVE_PATH = Path("secrets") / "ai-provider.local.json"
AiFeature = Literal[
    "resume",
    "job",
    "match",
    "ats",
    "tailor",
    "github",
    "career_advice",
    "source_import",
    "radar",
]


@dataclass(frozen=True)
class AiSettingsPaths:
    """Local filesystem paths used by the AI settings store."""

    settings: Path
    secrets: Path


@dataclass(frozen=True)
class AiRuntime:
    """Internal provider selection result. Never serialize this object to clients."""

    provider: AIProvider
    provider_name: str
    requested_provider: AiProvider
    model: str
    use_ai: bool
    configured: bool
    allowed: bool
    allow_memory_context: bool
    warnings: tuple[str, ...] = ()

    @property
    def fallback_used(self) -> bool:
        return self.requested_provider != "local" and self.provider_name == "local"

    @property
    def analysis_mode(self) -> str:
        if self.provider_name == "local":
            return "fallback" if self.fallback_used else "local"
        return "ai"


def get_ai_settings() -> AiSettingsResponse:
    """Return safe AI settings for frontend clients."""
    return AiSettingsStore.from_env().safe_settings()


def get_ai_settings_status() -> AiSettingsResponse:
    """Return the same safe status shape used by the settings screen."""
    return AiSettingsStore.from_env().safe_settings()


def save_ai_settings(payload: AiSettingsUpdateRequest) -> AiSettingsResponse:
    """Persist local provider settings and optional secret backend-side."""
    return AiSettingsStore.from_env().save(payload)


def test_ai_settings(payload: AiSettingsTestRequest) -> AiSettingsTestResponse:
    """Run a safe, user-triggered provider check."""
    return AiSettingsStore.from_env().test(payload)


def delete_ai_settings_secret() -> AiSettingsResponse:
    """Remove the stored AI provider key without exposing it."""
    return AiSettingsStore.from_env().delete_secret()


def get_ai_runtime(feature: AiFeature) -> AiRuntime:
    """Return an internal provider for one analysis area."""
    return AiSettingsStore.from_env().runtime(feature)


class AiSettingsStore:
    """File-backed local AI settings store.

    Metadata and secrets are split deliberately so the frontend can receive provider status
    without ever receiving the API key.
    """

    def __init__(self, paths: AiSettingsPaths) -> None:
        self.paths = paths

    @classmethod
    def from_env(cls) -> AiSettingsStore:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        return cls(
            AiSettingsPaths(
                settings=base / SETTINGS_RELATIVE_PATH,
                secrets=base / SECRETS_RELATIVE_PATH,
            )
        )

    def safe_settings(self) -> AiSettingsResponse:
        metadata = self._read_metadata()
        return self._to_response(metadata)

    def save(self, payload: AiSettingsUpdateRequest) -> AiSettingsResponse:
        metadata = {
            "provider": payload.provider,
            "model": _default_model(payload.provider, payload.model),
            "use_ai": payload.use_ai,
            "allow_match": payload.allow_match,
            "allow_ats": payload.allow_ats,
            "allow_tailor": payload.allow_tailor,
            "allow_github": payload.allow_github,
            "allow_memory_context": payload.allow_memory_context,
            "updated_at": _utc_now(),
        }

        cleaned_key = (payload.api_key or "").strip()
        if payload.provider == "gemini" and cleaned_key:
            self._write_secret(provider="gemini", api_key=cleaned_key)
        elif payload.provider != "gemini":
            self._delete_secret_file()

        self._write_json(self.paths.settings, metadata)
        return self._to_response(metadata)

    def test(self, payload: AiSettingsTestRequest) -> AiSettingsTestResponse:
        metadata = self._read_metadata()
        provider = payload.provider or _provider(metadata.get("provider"))
        model = _default_model(provider, payload.model or str(metadata.get("model", "")))

        if provider == "local":
            return AiSettingsTestResponse(
                provider=provider,
                model="local",
                success=True,
                configured=True,
                status="ready",
                message="Provider configurado com sucesso.",
            )

        if provider == "openai_future":
            return AiSettingsTestResponse(
                provider=provider,
                model=model,
                success=False,
                configured=False,
                status="planned",
                message="Provider planejado para uma versao futura.",
            )

        api_key = (payload.api_key or "").strip() or self._read_secret_for_provider("gemini")
        if not api_key:
            return AiSettingsTestResponse(
                provider="gemini",
                model=model,
                success=False,
                configured=False,
                status="not_configured",
                message="Nao foi possivel testar o provider. Verifique a chave e o modelo.",
            )

        diagnostic = self._test_gemini(api_key=api_key, model=model)
        success = bool(getattr(diagnostic, "success", False))
        return AiSettingsTestResponse(
            provider="gemini",
            model=model,
            success=success,
            configured=success,
            status="configured" if success else "error",
            message=(
                "Provider configurado com sucesso."
                if success
                else "Nao foi possivel testar o provider. Verifique a chave e o modelo."
            ),
        )

    def delete_secret(self) -> AiSettingsResponse:
        metadata = self._read_metadata()
        metadata["updated_at"] = _utc_now()
        metadata["use_ai"] = False
        self._delete_secret_file()
        self._write_json(self.paths.settings, metadata)
        return self._to_response(metadata)

    def runtime(self, feature: AiFeature) -> AiRuntime:
        metadata = self._read_metadata()
        settings = self._to_response(metadata)
        warnings = list(settings.warnings)
        allowed = _feature_allowed(settings, feature)
        requested_provider = settings.provider

        if not settings.use_ai or requested_provider == "local" or not allowed:
            if settings.use_ai and requested_provider != "local" and not allowed:
                warnings.append(f"IA desativada para {feature}; usei analise local.")
            return AiRuntime(
                provider=MockProvider(),
                provider_name="local",
                requested_provider=requested_provider,
                model="local",
                use_ai=settings.use_ai,
                configured=settings.configured,
                allowed=allowed,
                allow_memory_context=False,
                warnings=tuple(warnings),
            )

        if requested_provider == "openai_future":
            warnings.append("OpenAI ainda esta planejado; usei analise local.")
            return AiRuntime(
                provider=MockProvider(),
                provider_name="local",
                requested_provider=requested_provider,
                model="local",
                use_ai=settings.use_ai,
                configured=False,
                allowed=allowed,
                allow_memory_context=False,
                warnings=tuple(warnings),
            )

        api_key = self._read_secret_for_provider("gemini")
        if not api_key:
            warnings.append("Gemini sem chave no backend local; usei analise local.")
            return AiRuntime(
                provider=MockProvider(),
                provider_name="local",
                requested_provider="gemini",
                model="local",
                use_ai=settings.use_ai,
                configured=False,
                allowed=allowed,
                allow_memory_context=False,
                warnings=tuple(warnings),
            )

        provider = GeminiProvider(api_key=api_key, model=settings.model)
        return AiRuntime(
            provider=provider,
            provider_name=provider.name,
            requested_provider="gemini",
            model=provider.model,
            use_ai=settings.use_ai,
            configured=True,
            allowed=allowed,
            allow_memory_context=settings.allow_memory_context,
            warnings=tuple(warnings),
        )

    def _to_response(self, metadata: dict[str, Any]) -> AiSettingsResponse:
        provider = _provider(metadata.get("provider"))
        model = _default_model(provider, str(metadata.get("model", "")))
        configured = provider == "local" or (
            provider == "gemini" and bool(self._read_secret_for_provider("gemini"))
        )
        warnings: list[str] = []
        status = "ready"

        if provider == "gemini":
            status = "configured" if configured else "not_configured"
            if not configured:
                warnings.append("Gemini selecionado, mas nenhuma chave foi salva no backend local.")
        elif provider == "openai_future":
            configured = False
            status = "planned"
            warnings.append("OpenAI esta planejado para uma versao futura.")

        return AiSettingsResponse(
            provider=provider,
            model=model,
            configured=configured,
            status=status,
            use_ai=_bool(metadata.get("use_ai"), False),
            allow_match=_bool(metadata.get("allow_match"), True),
            allow_ats=_bool(metadata.get("allow_ats"), True),
            allow_tailor=_bool(metadata.get("allow_tailor"), True),
            allow_github=_bool(metadata.get("allow_github"), True),
            allow_memory_context=_bool(metadata.get("allow_memory_context"), False),
            updated_at=str(metadata.get("updated_at", "")),
            warnings=warnings,
        )

    def _test_gemini(self, *, api_key: str, model: str):
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(ai_setup.test_gemini_simple, api_key, model)
        try:
            return future.result(timeout=AI_TEST_TIMEOUT_SECONDS)
        except TimeoutError:
            future.cancel()
            return _DiagnosticFailure()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _read_metadata(self) -> dict[str, Any]:
        raw = self._read_json(self.paths.settings)
        defaults: dict[str, Any] = {
            "provider": "local",
            "model": "local",
            "use_ai": False,
            "allow_match": True,
            "allow_ats": True,
            "allow_tailor": True,
            "allow_github": True,
            "allow_memory_context": False,
            "updated_at": "",
        }
        defaults.update(raw)
        return defaults

    def _read_secret_for_provider(self, provider: AiProvider) -> str:
        raw = self._read_json(self.paths.secrets)
        if _provider(raw.get("provider")) != provider:
            return ""
        return str(raw.get("api_key", "")).strip()

    def _write_secret(self, *, provider: AiProvider, api_key: str) -> None:
        self._write_json(
            self.paths.secrets,
            {"provider": provider, "api_key": api_key, "updated_at": _utc_now()},
        )
        with suppress(OSError):
            os.chmod(self.paths.secrets, 0o600)

    def _delete_secret_file(self) -> None:
        with suppress(FileNotFoundError):
            self.paths.secrets.unlink()

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class _DiagnosticFailure:
    success = False


def _provider(value: object) -> AiProvider:
    raw = str(value or "local").strip().lower()
    if raw in {"local", "gemini", "openai_future"}:
        return raw  # type: ignore[return-value]
    return "local"


def _default_model(provider: AiProvider, model: str | None = None) -> str:
    cleaned = (model or "").strip()
    if provider == "local":
        return "local"
    if provider == "gemini":
        return cleaned or ai_setup.DEFAULT_GEMINI_MODEL
    return cleaned or "planned"


def _bool(value: object, fallback: bool) -> bool:
    return value if isinstance(value, bool) else fallback


def _feature_allowed(settings: AiSettingsResponse, feature: AiFeature) -> bool:
    if feature == "match":
        return settings.allow_match
    if feature == "ats":
        return settings.allow_ats
    if feature == "tailor":
        return settings.allow_tailor
    if feature == "github":
        return settings.allow_github
    return True


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def validate_safe_response(data: dict[str, Any]) -> AiSettingsResponse:
    """Small helper used by tests and future integrations."""
    try:
        return AiSettingsResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError("AI settings response contains unsafe or invalid fields.") from exc
