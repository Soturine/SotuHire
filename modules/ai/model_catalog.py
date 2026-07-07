"""Local-first AI provider and model catalog."""

from __future__ import annotations

import importlib
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CatalogProvider = Literal["local", "gemini", "openai"]

MODEL_CACHE_RELATIVE_PATH = Path("settings") / "ai-models-cache.json"
GEMINI_KEY_URL = "https://aistudio.google.com/app/apikey"
OPENAI_KEY_URL = "https://platform.openai.com/api-keys"


class CatalogModel(BaseModel):
    """One safe model entry exposed to the settings UI."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    status: str = "known"
    supports_structured_output: bool = True
    supports_json: bool = True
    recommended_for: list[str] = Field(default_factory=list)


class CatalogProviderInfo(BaseModel):
    """Safe provider summary for frontend settings."""

    model_config = ConfigDict(extra="forbid")

    id: CatalogProvider
    label: str
    status: str = "available"
    requires_api_key: bool = False
    key_url: str = ""
    supports_model_catalog: bool = False
    warnings: list[str] = Field(default_factory=list)


class CatalogResult(BaseModel):
    """Model catalog result with source metadata."""

    model_config = ConfigDict(extra="forbid")

    provider: CatalogProvider
    models: list[CatalogModel] = Field(default_factory=list)
    source: str = "builtin"
    updated_at: str = ""
    warnings: list[str] = Field(default_factory=list)


BUILTIN_MODELS: dict[CatalogProvider, list[CatalogModel]] = {
    "local": [
        CatalogModel(
            id="local",
            label="Análise local",
            status="known",
            supports_structured_output=False,
            supports_json=True,
            recommended_for=["safe", "offline", "fallback"],
        )
    ],
    "gemini": [
        CatalogModel(
            id="gemini-2.5-flash",
            label="Gemini 2.5 Flash",
            recommended_for=["fast", "cost_effective", "general"],
        ),
        CatalogModel(
            id="gemini-2.5-pro",
            label="Gemini 2.5 Pro",
            recommended_for=["reasoning", "long_context", "review"],
        ),
        CatalogModel(
            id="gemini-1.5-flash",
            label="Gemini 1.5 Flash",
            recommended_for=["compatibility", "fallback"],
        ),
    ],
    "openai": [
        CatalogModel(
            id="gpt-5-mini",
            label="GPT-5 mini",
            recommended_for=["fast", "cost_effective", "general"],
        ),
        CatalogModel(
            id="gpt-5",
            label="GPT-5",
            recommended_for=["reasoning", "structured_output", "review"],
        ),
        CatalogModel(
            id="gpt-4.1-mini",
            label="GPT-4.1 mini",
            recommended_for=["compatibility", "fast"],
        ),
        CatalogModel(
            id="gpt-4.1",
            label="GPT-4.1",
            recommended_for=["compatibility", "structured_output"],
        ),
    ],
}


def providers_catalog(*, configured: dict[str, bool] | None = None) -> list[CatalogProviderInfo]:
    """Return safe provider metadata without secrets."""
    configured = configured or {}
    return [
        CatalogProviderInfo(
            id="local",
            label="Local seguro",
            status="ready",
            requires_api_key=False,
            supports_model_catalog=False,
        ),
        CatalogProviderInfo(
            id="gemini",
            label="Gemini",
            status="configured" if configured.get("gemini") else "not_configured",
            requires_api_key=True,
            key_url=GEMINI_KEY_URL,
            supports_model_catalog=True,
        ),
        CatalogProviderInfo(
            id="openai",
            label="OpenAI",
            status="configured" if configured.get("openai") else "not_configured",
            requires_api_key=True,
            key_url=OPENAI_KEY_URL,
            supports_model_catalog=True,
        ),
    ]


def list_models(provider: str, *, cache_path: str | Path | None = None) -> CatalogResult:
    """List models from local cache when present, falling back to builtin entries."""
    normalized = normalize_provider(provider)
    cached = _read_cached_models(normalized, _cache_path(cache_path))
    if cached:
        return cached
    return CatalogResult(
        provider=normalized,
        models=list(BUILTIN_MODELS[normalized]),
        source="builtin",
        updated_at="",
        warnings=[],
    )


def refresh_models(
    provider: str,
    *,
    api_key: str = "",
    cache_path: str | Path | None = None,
) -> CatalogResult:
    """Try a user-triggered provider refresh, preserving builtin/cache on failure."""
    normalized = normalize_provider(provider)
    path = _cache_path(cache_path)
    warnings: list[str] = []
    if normalized == "local":
        return list_models("local", cache_path=path)
    if not api_key.strip():
        result = list_models(normalized, cache_path=path)
        return result.model_copy(
            update={
                "warnings": [
                    *result.warnings,
                    "Chave ausente no backend local; mantive catálogo local/builtin.",
                ]
            }
        )

    try:
        provider_models = (
            _fetch_gemini_models(api_key.strip())
            if normalized == "gemini"
            else _fetch_openai_models(api_key.strip())
        )
        if not provider_models:
            raise ValueError("Provider não retornou modelos compatíveis.")
        result = CatalogResult(
            provider=normalized,
            models=provider_models,
            source="provider_api",
            updated_at=_utc_now(),
            warnings=[],
        )
        _write_cached_models(path, result)
        return result
    except Exception as exc:
        warnings.append(
            f"Não foi possível atualizar modelos via provider; mantive cache/builtin. Motivo: {type(exc).__name__}."
        )
        result = list_models(normalized, cache_path=path)
        return result.model_copy(update={"warnings": [*result.warnings, *warnings]})


def normalize_provider(provider: str) -> CatalogProvider:
    """Normalize provider ids and legacy aliases."""
    raw = (provider or "local").strip().lower()
    if raw == "openai_future":
        raw = "openai"
    if raw in {"local", "gemini", "openai"}:
        return raw  # type: ignore[return-value]
    return "local"


def _fetch_gemini_models(api_key: str) -> list[CatalogModel]:
    genai = importlib.import_module("google.genai")
    client = genai.Client(api_key=api_key)
    models = client.models.list()
    entries: list[CatalogModel] = []
    for model in models:
        raw_name = str(getattr(model, "name", "") or getattr(model, "id", "") or "")
        model_id = raw_name.rsplit("/", 1)[-1]
        if not model_id or "gemini" not in model_id:
            continue
        actions = [str(item) for item in getattr(model, "supported_actions", []) or []]
        if actions and not any("generate" in item.lower() for item in actions):
            continue
        entries.append(
            CatalogModel(
                id=model_id,
                label=_label_from_model_id(model_id),
                status="provider_api",
                recommended_for=["provider_api"],
            )
        )
    return _dedupe_models(entries)


def _fetch_openai_models(api_key: str) -> list[CatalogModel]:
    request = urllib.request.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError("OpenAI model list request failed.") from exc
    data = payload.get("data", []) if isinstance(payload, dict) else []
    entries: list[CatalogModel] = []
    for item in data:
        model_id = str(item.get("id", "")) if isinstance(item, dict) else ""
        if not model_id.startswith(("gpt-", "o")):
            continue
        entries.append(
            CatalogModel(
                id=model_id,
                label=_label_from_model_id(model_id),
                status="provider_api",
                recommended_for=["provider_api"],
            )
        )
    return _dedupe_models(entries)


def _read_cached_models(provider: CatalogProvider, path: Path) -> CatalogResult | None:
    raw = _read_json(path)
    providers = raw.get("providers", {})
    if not isinstance(providers, dict):
        return None
    payload = providers.get(provider, {})
    if not isinstance(payload, dict):
        return None
    try:
        result = CatalogResult.model_validate({"provider": provider, **payload})
    except ValueError:
        return None
    if not result.models:
        return None
    return result.model_copy(update={"source": "cache"})


def _write_cached_models(path: Path, result: CatalogResult) -> None:
    raw = _read_json(path)
    providers = raw.get("providers", {})
    if not isinstance(providers, dict):
        providers = {}
    providers[result.provider] = {
        "models": [model.model_dump(mode="json") for model in result.models],
        "source": "cache",
        "updated_at": result.updated_at,
        "warnings": result.warnings,
    }
    raw["providers"] = providers
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _cache_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
    return base / MODEL_CACHE_RELATIVE_PATH


def _dedupe_models(models: list[CatalogModel]) -> list[CatalogModel]:
    by_id: dict[str, CatalogModel] = {model.id: model for model in BUILTIN_MODELS["local"][:0]}
    for model in [*models]:
        by_id.setdefault(model.id, model)
    return sorted(by_id.values(), key=lambda item: item.id)


def _label_from_model_id(model_id: str) -> str:
    return model_id.replace("-", " ").replace("_", " ").title()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
