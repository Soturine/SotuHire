"""Local configuration and status helpers for the optional Gemini provider."""

from __future__ import annotations

import importlib.util
import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_SECRETS_PATH = Path(".streamlit/secrets.toml")


class GeminiSetupStatus(BaseModel):
    """Friendly Gemini availability status for the setup wizard."""

    model_config = ConfigDict(extra="forbid")

    key_configured: bool
    sdk_installed: bool
    available: bool
    message: str
    reason: str = ""


class GeminiTestResult(BaseModel):
    """Result of an explicit user-triggered Gemini connection test."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    message: str
    detail: str = ""


def _read_local_secrets(path: str | Path = DEFAULT_SECRETS_PATH) -> dict[str, object]:
    target = Path(path)
    if not target.exists():
        return {}
    try:
        with target.open("rb") as file:
            return tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def gemini_api_key(explicit: str | None = None) -> str:
    """Resolve Gemini credentials while keeping legacy aliases compatible."""
    if explicit is not None:
        return explicit.strip()
    secrets = _read_local_secrets()
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or str(secrets.get("GEMINI_API_KEY", ""))
    ).strip()


def gemini_model(explicit: str | None = None) -> str:
    """Resolve the configured Gemini model with the legacy model alias."""
    if explicit:
        return explicit.strip()
    secrets = _read_local_secrets()
    return (
        os.getenv("GEMINI_MODEL")
        or os.getenv("LLM_MODEL")
        or str(secrets.get("GEMINI_MODEL", ""))
        or DEFAULT_GEMINI_MODEL
    ).strip()


def gemini_sdk_installed() -> bool:
    """Return whether the optional Google Gen AI SDK can be imported."""
    try:
        return importlib.util.find_spec("google.genai") is not None
    except ModuleNotFoundError:
        return False


def gemini_setup_status(api_key: str | None = None) -> GeminiSetupStatus:
    """Describe whether Gemini can currently be used."""
    key_configured = bool(gemini_api_key(api_key))
    sdk_installed = gemini_sdk_installed()
    if not key_configured:
        return GeminiSetupStatus(
            key_configured=False,
            sdk_installed=sdk_installed,
            available=False,
            message="Gemini indisponível. Usando análise local.",
            reason="chave ausente",
        )
    if not sdk_installed:
        return GeminiSetupStatus(
            key_configured=True,
            sdk_installed=False,
            available=False,
            message="Gemini indisponível. Usando análise local.",
            reason="SDK ausente. Instale com: pip install -r requirements-ai.txt",
        )
    return GeminiSetupStatus(
        key_configured=True,
        sdk_installed=True,
        available=True,
        message="Gemini configurado e ativo.",
    )


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def save_local_ai_config(
    api_key: str,
    *,
    provider: str = "gemini",
    model: str = DEFAULT_GEMINI_MODEL,
    path: str | Path = DEFAULT_SECRETS_PATH,
) -> Path:
    """Save non-versioned local AI configuration and activate it in this process."""
    cleaned_key = api_key.strip()
    if not cleaned_key:
        raise ValueError("Cole uma chave Gemini antes de salvar.")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            [
                f"DEFAULT_AI_PROVIDER = {_toml_string(provider)}",
                f"GEMINI_API_KEY = {_toml_string(cleaned_key)}",
                f"GEMINI_MODEL = {_toml_string(model)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    os.environ["DEFAULT_AI_PROVIDER"] = provider
    os.environ["GEMINI_API_KEY"] = cleaned_key
    os.environ["GEMINI_MODEL"] = model
    return target


def test_gemini_connection(api_key: str) -> GeminiTestResult:
    """Run a small explicit Gemini request and return a friendly result."""
    status = gemini_setup_status(api_key)
    if not status.available:
        return GeminiTestResult(success=False, message=status.message, detail=status.reason)
    try:
        from modules.ai.providers.gemini_provider import GeminiProvider

        GeminiProvider(api_key=api_key).analyze(
            "Pessoa candidata com Python.",
            "Vaga júnior para Python.",
        )
    except Exception as exc:
        detail = " ".join(str(exc).split())[:240] or exc.__class__.__name__
        return GeminiTestResult(
            success=False,
            message="Não foi possível autenticar no Gemini.",
            detail=detail,
        )
    return GeminiTestResult(success=True, message="Gemini configurado e ativo.")
