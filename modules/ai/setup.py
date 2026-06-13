"""Local configuration and status helpers for the optional Gemini provider."""

from __future__ import annotations

import importlib.util
import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from modules.ai.diagnostics import GeminiDiagnostic, diagnose_gemini_error, successful_diagnostic

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
SUPPORTED_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"]
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


def gemini_key_source(explicit: str | None = None) -> str:
    """Return which supported location supplied the key, without exposing it."""
    if explicit is not None and explicit.strip():
        return "campo seguro da interface"
    if os.getenv("GEMINI_API_KEY", "").strip():
        return "GEMINI_API_KEY"
    if os.getenv("GOOGLE_API_KEY", "").strip():
        return "GOOGLE_API_KEY (alias)"
    if str(_read_local_secrets().get("GEMINI_API_KEY", "")).strip():
        return ".streamlit/secrets.toml"
    return "não encontrada"


def _read_local_secrets(path: str | Path | None = None) -> dict[str, object]:
    target = Path(path or DEFAULT_SECRETS_PATH)
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


def default_ai_provider(explicit: str | None = None) -> str:
    """Resolve the selected provider from canonical config or legacy alias."""
    if explicit:
        return explicit.strip().lower()
    secrets = _read_local_secrets()
    return (
        (
            os.getenv("DEFAULT_AI_PROVIDER")
            or os.getenv("LLM_PROVIDER")
            or str(secrets.get("DEFAULT_AI_PROVIDER", ""))
            or "local"
        )
        .strip()
        .lower()
    )


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
        message="Gemini configurado e pronto para uso.",
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


def test_gemini_simple(api_key: str, model: str | None = None) -> GeminiDiagnostic:
    """Test key/model/SDK using a minimal call without structured output."""
    status = gemini_setup_status(api_key)
    if not status.available:
        return GeminiDiagnostic(
            success=False,
            test_type="simple",
            summary=status.reason,
            category=status.reason,
            model=gemini_model(model),
            sdk_version="não instalado" if not status.sdk_installed else "instalado",
            key_source=gemini_key_source(api_key),
            call_type="generate_content sem schema",
        )
    try:
        from modules.ai.providers.gemini_provider import GeminiProvider

        provider = GeminiProvider(api_key=api_key, model=model)
        provider.ping()
    except Exception as exc:
        return diagnose_gemini_error(
            exc,
            test_type="simple",
            model=gemini_model(model),
            key_source=gemini_key_source(api_key),
            call_type="generate_content sem schema",
        )
    return successful_diagnostic(
        test_type="simple",
        model=gemini_model(model),
        key_source=gemini_key_source(api_key),
        call_type="generate_content sem schema",
    )


def test_gemini_structured(api_key: str, model: str | None = None) -> GeminiDiagnostic:
    """Test the exact structured-output path used by SotuHire."""
    status = gemini_setup_status(api_key)
    if not status.available:
        return GeminiDiagnostic(
            success=False,
            test_type="structured",
            summary=status.reason,
            category=status.reason,
            model=gemini_model(model),
            sdk_version="não instalado" if not status.sdk_installed else "instalado",
            key_source=gemini_key_source(api_key),
            call_type="generate_content com response_json_schema",
        )
    try:
        from modules.ai.providers.gemini_provider import GeminiProvider

        GeminiProvider(api_key=api_key, model=model).analyze(
            "Pessoa candidata com Python.",
            "Vaga júnior para Python.",
        )
    except Exception as exc:
        return diagnose_gemini_error(
            exc,
            test_type="structured",
            model=gemini_model(model),
            key_source=gemini_key_source(api_key),
            call_type="generate_content com response_json_schema",
        )
    return successful_diagnostic(
        test_type="structured",
        model=gemini_model(model),
        key_source=gemini_key_source(api_key),
        call_type="generate_content com response_json_schema",
    )


def test_gemini_analysis(api_key: str, model: str | None = None) -> GeminiDiagnostic:
    """Test the same provider analysis call used by the application."""
    status = gemini_setup_status(api_key)
    if not status.available:
        return GeminiDiagnostic(
            success=False,
            test_type="analysis",
            summary=status.reason,
            category=status.reason,
            model=gemini_model(model),
            sdk_version="não instalado" if not status.sdk_installed else "instalado",
            key_source=gemini_key_source(api_key),
            call_type="análise real do SotuHire",
        )
    try:
        from modules.ai.providers.gemini_provider import GeminiProvider

        GeminiProvider(api_key=api_key, model=model).analyze(
            "Currículo fictício: pessoa desenvolvedora júnior com Python e SQL.",
            "Vaga fictícia: pessoa desenvolvedora júnior com Python.",
        )
    except Exception as exc:
        return diagnose_gemini_error(
            exc,
            test_type="analysis",
            model=gemini_model(model),
            key_source=gemini_key_source(api_key),
            call_type="análise real do SotuHire",
        )
    return successful_diagnostic(
        test_type="analysis",
        model=gemini_model(model),
        key_source=gemini_key_source(api_key),
        call_type="análise real do SotuHire",
    )


def test_gemini_connection(api_key: str) -> GeminiTestResult:
    """Backward-compatible wrapper around the structured Gemini test."""
    diagnostic = test_gemini_structured(api_key)
    return GeminiTestResult(
        success=diagnostic.success,
        message=(
            "Gemini configurado e ativo."
            if diagnostic.success
            else "Não foi possível autenticar no Gemini."
        ),
        detail=diagnostic.raw_error or diagnostic.category,
    )
