"""Safe, structured diagnostics for optional Gemini calls."""

from __future__ import annotations

import importlib.metadata
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict

GeminiTestType = Literal["simple", "structured", "analysis"]


class GeminiDiagnostic(BaseModel):
    """Sanitized Gemini call result that never includes the API key."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    test_type: GeminiTestType
    summary: str
    code: str = ""
    category: str = ""
    model: str
    sdk_version: str
    key_source: str
    call_type: str
    suggestion: str = ""
    raw_error: str = ""


def google_genai_version() -> str:
    """Return the installed SDK version without importing provider internals."""
    try:
        return importlib.metadata.version("google-genai")
    except importlib.metadata.PackageNotFoundError:
        return "não instalado"


def diagnose_gemini_error(
    exc: Exception,
    *,
    test_type: GeminiTestType,
    model: str,
    key_source: str,
    call_type: str,
) -> GeminiDiagnostic:
    """Classify a Gemini failure into an actionable, sanitized diagnostic."""
    raw = " ".join(str(exc).split())[:600] or exc.__class__.__name__
    upper = raw.upper()
    code_match = re.search(r"\b(\d{3}\s+[A-Z][A-Z_]+)\b", upper)
    code = code_match.group(1) if code_match else ""

    if key_source == "não encontrada":
        category = "chave ausente"
    elif "API_KEY" in upper or "API KEY" in upper or "UNAUTHENTICATED" in upper:
        category = "chave inválida ou não autorizada"
    elif "MODEL" in upper and any(term in upper for term in ["NOT FOUND", "NOT_FOUND", "INVALID"]):
        category = "modelo inválido ou indisponível"
    elif "QUOTA" in upper or "RESOURCE_EXHAUSTED" in upper:
        category = "quota ou limite do projeto"
    elif "REGION" in upper or "LOCATION" in upper:
        category = "região ou projeto incompatível"
    elif "INVALID_ARGUMENT" in upper:
        category = (
            "schema ou payload estruturado incompatível"
            if test_type == "structured"
            else "modelo, payload ou configuração incompatível"
        )
    elif "SAFETY" in upper:
        category = "configuração de safety"
    else:
        category = "erro inesperado do Gemini"

    suggestion = ""
    if "INVALID_ARGUMENT" in upper:
        suggestion = (
            "Teste outro modelo. Se o teste simples passar e este falhar, revise o schema."
            if test_type == "structured"
            else "Teste outro modelo configurado no wizard."
        )

    return GeminiDiagnostic(
        success=False,
        test_type=test_type,
        summary=category,
        code=code,
        category=category,
        model=model,
        sdk_version=google_genai_version(),
        key_source=key_source,
        call_type=call_type,
        suggestion=suggestion,
        raw_error=raw,
    )


def successful_diagnostic(
    *,
    test_type: GeminiTestType,
    model: str,
    key_source: str,
    call_type: str,
) -> GeminiDiagnostic:
    """Build a successful Gemini diagnostic."""
    return GeminiDiagnostic(
        success=True,
        test_type=test_type,
        summary="Gemini respondeu corretamente.",
        model=model,
        sdk_version=google_genai_version(),
        key_source=key_source,
        call_type=call_type,
    )
