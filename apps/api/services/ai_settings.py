"""Secure local storage and diagnostics for AI provider settings."""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from modules.ai import model_catalog
from modules.ai import setup as ai_setup
from modules.ai.providers import AIProvider, GeminiProvider, MockProvider, OpenAIProvider
from modules.ai.providers.openai_provider import DEFAULT_OPENAI_MODEL
from pydantic import ValidationError

from apps.api.schemas.settings import (
    AiModelsRefreshRequest,
    AiModelsResponse,
    AiProvider,
    AiProvidersResponse,
    AiSettingsPreset,
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
    "public_exams",
    "profile",
    "lattes",
    "extension",
    "notifications",
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
    model_requested: str
    use_ai: bool
    configured: bool
    allowed: bool
    allow_memory_context: bool
    warnings: tuple[str, ...] = ()
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_monotonic: float = field(default_factory=time.perf_counter)

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


def list_ai_providers() -> AiProvidersResponse:
    """Return safe AI providers metadata for frontend clients."""
    return AiSettingsStore.from_env().providers()


def list_ai_models(provider: str) -> AiModelsResponse:
    """Return builtin/cache model catalog for one provider."""
    return AiSettingsStore.from_env().models(provider)


def refresh_ai_models(payload: AiModelsRefreshRequest) -> AiModelsResponse:
    """Refresh provider models only after explicit user action."""
    return AiSettingsStore.from_env().refresh_models(payload.provider)


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
        normalized_provider = _provider(payload.provider)
        settings = _settings_from_payload(payload, normalized_provider)
        metadata = {
            "provider": normalized_provider,
            "model": _default_model(normalized_provider, payload.model),
            "preset": settings["preset"],
            "use_ai": settings["use_ai"],
            "allow_profile": settings["allow_profile"],
            "allow_lattes": settings["allow_lattes"],
            "allow_resume": settings["allow_resume"],
            "allow_job": settings["allow_job"],
            "allow_public_exams": settings["allow_public_exams"],
            "allow_match": settings["allow_match"],
            "allow_ats": settings["allow_ats"],
            "allow_tailor": settings["allow_tailor"],
            "allow_github": settings["allow_github"],
            "allow_source_import": settings["allow_source_import"],
            "allow_extension": settings["allow_extension"],
            "allow_radar": settings["allow_radar"],
            "allow_notifications": settings["allow_notifications"],
            "allow_memory_context": settings["allow_memory_context"],
            "updated_at": _utc_now(),
        }

        cleaned_key = (payload.api_key or "").strip()
        if normalized_provider in {"gemini", "openai"} and cleaned_key:
            self._write_secret(provider=normalized_provider, api_key=cleaned_key)

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

        secret_provider = "openai" if provider == "openai_future" else provider
        api_key = (payload.api_key or "").strip() or self._read_secret_for_provider(secret_provider)
        if not api_key:
            return AiSettingsTestResponse(
                provider=provider,
                model=model,
                success=False,
                configured=False,
                status="not_configured",
                message="Nao foi possivel testar o provider. Verifique a chave e o modelo.",
            )

        diagnostic = (
            self._test_gemini(api_key=api_key, model=model)
            if provider == "gemini"
            else self._test_openai(api_key=api_key, model=model)
        )
        success = bool(getattr(diagnostic, "success", False))
        return AiSettingsTestResponse(
            provider=provider,
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

    def providers(self) -> AiProvidersResponse:
        """Return safe provider status and key URLs."""
        configured = {
            "gemini": bool(self._read_secret_for_provider("gemini")),
            "openai": bool(self._read_secret_for_provider("openai")),
        }
        return AiProvidersResponse.model_validate(
            {
                "providers": [
                    provider.model_dump(mode="json")
                    for provider in model_catalog.providers_catalog(configured=configured)
                ]
            }
        )

    def models(self, provider: str) -> AiModelsResponse:
        """Return local model catalog without calling external providers."""
        result = model_catalog.list_models(provider, cache_path=self._models_cache_path())
        return AiModelsResponse.model_validate(result.model_dump(mode="json"))

    def refresh_models(self, provider: str) -> AiModelsResponse:
        """Refresh one provider catalog using a backend-stored key when available."""
        normalized = model_catalog.normalize_provider(provider)
        result = model_catalog.refresh_models(
            normalized,
            api_key=self._read_secret_for_provider(normalized),
            cache_path=self._models_cache_path(),
        )
        return AiModelsResponse.model_validate(result.model_dump(mode="json"))

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
                model_requested=settings.model,
                use_ai=settings.use_ai,
                configured=settings.configured,
                allowed=allowed,
                allow_memory_context=False,
                warnings=tuple(warnings),
            )

        secret_provider = "openai" if requested_provider == "openai_future" else requested_provider
        api_key = self._read_secret_for_provider(secret_provider)
        if not api_key:
            warnings.append(
                f"{provider_label(secret_provider)} sem chave no backend local; usei analise local."
            )
            return AiRuntime(
                provider=MockProvider(),
                provider_name="local",
                requested_provider=requested_provider,
                model="local",
                model_requested=settings.model,
                use_ai=settings.use_ai,
                configured=False,
                allowed=allowed,
                allow_memory_context=False,
                warnings=tuple(warnings),
            )

        provider = (
            GeminiProvider(api_key=api_key, model=settings.model)
            if secret_provider == "gemini"
            else OpenAIProvider(api_key=api_key, model=settings.model)
        )
        return AiRuntime(
            provider=provider,
            provider_name=provider.name,
            requested_provider=requested_provider,
            model=provider.model,
            model_requested=settings.model,
            use_ai=settings.use_ai,
            configured=True,
            allowed=allowed,
            allow_memory_context=settings.allow_memory_context,
            warnings=tuple(warnings),
        )

    def _to_response(self, metadata: dict[str, Any]) -> AiSettingsResponse:
        raw_provider = str(metadata.get("provider", "local"))
        provider = _provider(metadata.get("provider"))
        model = _default_model(provider, str(metadata.get("model", "")))
        secret_provider = "openai" if provider == "openai_future" else provider
        configured = provider == "local" or (
            secret_provider in {"gemini", "openai"}
            and bool(self._read_secret_for_provider(secret_provider))
        )
        warnings: list[str] = []
        status = "ready"

        if provider == "gemini":
            status = "configured" if configured else "not_configured"
            if not configured:
                warnings.append("Gemini selecionado, mas nenhuma chave foi salva no backend local.")
        elif provider in {"openai", "openai_future"}:
            status = "configured" if configured else "not_configured"
            if raw_provider.strip().lower() == "openai_future":
                warnings.append("openai_future foi migrado para OpenAI real no backend local.")
            if not configured:
                warnings.append("OpenAI selecionado, mas nenhuma chave foi salva no backend local.")

        return AiSettingsResponse(
            provider=provider,
            model=model,
            configured=configured,
            status=status,
            preset=_preset(metadata.get("preset")),
            use_ai=_bool(metadata.get("use_ai"), False),
            allow_profile=_bool(metadata.get("allow_profile"), True),
            allow_lattes=_bool(metadata.get("allow_lattes"), True),
            allow_resume=_bool(metadata.get("allow_resume"), True),
            allow_job=_bool(metadata.get("allow_job"), True),
            allow_public_exams=_bool(
                metadata.get("allow_public_exams"),
                _bool(metadata.get("allow_radar"), True),
            ),
            allow_match=_bool(metadata.get("allow_match"), True),
            allow_ats=_bool(metadata.get("allow_ats"), True),
            allow_tailor=_bool(metadata.get("allow_tailor"), True),
            allow_github=_bool(metadata.get("allow_github"), True),
            allow_source_import=_bool(metadata.get("allow_source_import"), True),
            allow_extension=_bool(metadata.get("allow_extension"), True),
            allow_radar=_bool(metadata.get("allow_radar"), True),
            allow_notifications=_bool(metadata.get("allow_notifications"), True),
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

    def _test_openai(self, *, api_key: str, model: str):
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(OpenAIProvider(api_key=api_key, model=model).ping)
        try:
            future.result(timeout=AI_TEST_TIMEOUT_SECONDS)
            return _DiagnosticSuccess()
        except Exception:
            future.cancel()
            return _DiagnosticFailure()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _read_metadata(self) -> dict[str, Any]:
        raw = self._read_json(self.paths.settings)
        defaults: dict[str, Any] = {
            "provider": "local",
            "model": "local",
            "preset": "local_safe",
            "use_ai": False,
            "allow_profile": True,
            "allow_lattes": True,
            "allow_resume": True,
            "allow_job": True,
            "allow_public_exams": True,
            "allow_match": True,
            "allow_ats": True,
            "allow_tailor": True,
            "allow_github": True,
            "allow_source_import": True,
            "allow_extension": True,
            "allow_radar": True,
            "allow_notifications": True,
            "allow_memory_context": False,
            "updated_at": "",
        }
        defaults.update(raw)
        return defaults

    def _read_secret_for_provider(self, provider: str) -> str:
        raw = self._read_json(self.paths.secrets)
        normalized = _provider(provider)
        providers = raw.get("providers", {})
        if isinstance(providers, dict):
            entry = providers.get(normalized, {})
            if isinstance(entry, dict):
                return str(entry.get("api_key", "")).strip()
        if _provider(raw.get("provider")) == normalized:
            return str(raw.get("api_key", "")).strip()
        return ""

    def _write_secret(self, *, provider: str, api_key: str) -> None:
        raw = self._read_json(self.paths.secrets)
        providers = raw.get("providers", {})
        if not isinstance(providers, dict):
            providers = {}
        legacy_provider = raw.get("provider")
        legacy_key = raw.get("api_key")
        if legacy_provider and legacy_key:
            providers[_provider(legacy_provider)] = {
                "api_key": str(legacy_key),
                "updated_at": str(raw.get("updated_at", "")),
            }
        providers[_provider(provider)] = {"api_key": api_key, "updated_at": _utc_now()}
        self._write_json(self.paths.secrets, {"providers": providers, "updated_at": _utc_now()})
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

    def _models_cache_path(self) -> Path:
        return self.paths.settings.parent / "ai-models-cache.json"


class _DiagnosticFailure:
    success = False


class _DiagnosticSuccess:
    success = True


def _provider(value: object) -> AiProvider:
    raw = str(value or "local").strip().lower()
    if raw == "openai_future":
        return "openai"
    if raw in {"local", "gemini", "openai"}:
        return raw  # type: ignore[return-value]
    return "local"


def _default_model(provider: AiProvider, model: str | None = None) -> str:
    cleaned = (model or "").strip()
    if provider == "local":
        return "local"
    if provider == "gemini":
        return cleaned or ai_setup.DEFAULT_GEMINI_MODEL
    if provider in {"openai", "openai_future"}:
        return cleaned or DEFAULT_OPENAI_MODEL
    return cleaned or "local"


def _preset(value: object) -> AiSettingsPreset:
    raw = str(value or "local_safe").strip().lower()
    if raw in {"local_safe", "basic", "complete", "custom"}:
        return cast(AiSettingsPreset, raw)
    return "custom"


def _settings_from_payload(
    payload: AiSettingsUpdateRequest,
    provider: AiProvider,
) -> dict[str, bool | str]:
    preset = _preset(payload.preset)
    if preset == "local_safe":
        return {
            **_feature_defaults(enabled=False),
            "preset": preset,
            "use_ai": False,
            "allow_memory_context": False,
        }
    if preset == "basic":
        values = _feature_defaults(enabled=False)
        values.update(
            {
                "preset": preset,
                "use_ai": provider != "local",
                "allow_profile": True,
                "allow_lattes": True,
                "allow_resume": True,
                "allow_job": True,
                "allow_public_exams": True,
                "allow_match": True,
                "allow_ats": True,
                "allow_tailor": True,
                "allow_memory_context": False,
            }
        )
        return values
    if preset == "complete":
        values = _feature_defaults(enabled=True)
        values.update(
            {
                "preset": preset,
                "use_ai": provider != "local",
                "allow_memory_context": bool(payload.allow_memory_context),
            }
        )
        return values
    return {
        "preset": "custom",
        "use_ai": bool(payload.use_ai and provider != "local"),
        "allow_profile": payload.allow_profile,
        "allow_lattes": payload.allow_lattes,
        "allow_resume": payload.allow_resume,
        "allow_job": payload.allow_job,
        "allow_public_exams": payload.allow_public_exams,
        "allow_match": payload.allow_match,
        "allow_ats": payload.allow_ats,
        "allow_tailor": payload.allow_tailor,
        "allow_github": payload.allow_github,
        "allow_source_import": payload.allow_source_import,
        "allow_extension": payload.allow_extension,
        "allow_radar": payload.allow_radar,
        "allow_notifications": payload.allow_notifications,
        "allow_memory_context": payload.allow_memory_context,
    }


def _feature_defaults(*, enabled: bool) -> dict[str, bool | str]:
    return {
        "allow_profile": enabled,
        "allow_lattes": enabled,
        "allow_resume": enabled,
        "allow_job": enabled,
        "allow_public_exams": enabled,
        "allow_match": enabled,
        "allow_ats": enabled,
        "allow_tailor": enabled,
        "allow_github": enabled,
        "allow_source_import": enabled,
        "allow_extension": enabled,
        "allow_radar": enabled,
        "allow_notifications": enabled,
        "allow_memory_context": False,
    }


def _bool(value: object, fallback: bool) -> bool:
    return value if isinstance(value, bool) else fallback


def _feature_allowed(settings: AiSettingsResponse, feature: AiFeature) -> bool:
    if feature == "resume":
        return settings.allow_resume
    if feature == "job":
        return settings.allow_job
    if feature == "public_exams":
        return settings.allow_public_exams
    if feature == "match":
        return settings.allow_match
    if feature == "ats":
        return settings.allow_ats
    if feature == "tailor":
        return settings.allow_tailor
    if feature == "github":
        return settings.allow_github
    if feature == "source_import":
        return settings.allow_source_import
    if feature == "radar":
        return settings.allow_radar
    if feature == "profile":
        return settings.allow_profile
    if feature == "lattes":
        return settings.allow_lattes
    if feature == "extension":
        return settings.allow_extension
    if feature == "notifications":
        return settings.allow_notifications
    return True


def provider_label(provider: str) -> str:
    if provider == "openai":
        return "OpenAI"
    if provider == "gemini":
        return "Gemini"
    return "Provider local"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def validate_safe_response(data: dict[str, Any]) -> AiSettingsResponse:
    """Small helper used by tests and future integrations."""
    try:
        return AiSettingsResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError("AI settings response contains unsafe or invalid fields.") from exc
