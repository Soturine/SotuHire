"""Optional AI-assisted resume extraction with deterministic local fallback."""

from __future__ import annotations

import importlib
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict

from modules.ai.setup import gemini_api_key, gemini_model
from modules.parsers.resume_parser import parse_resume_text
from modules.schemas.resume_profile import ResumeProfileSchema

AIResumeGenerator = Callable[[str], ResumeProfileSchema]
LIST_FIELDS = (
    "education",
    "experiences",
    "projects",
    "courses",
    "certifications",
    "skills",
    "soft_skills",
    "languages",
    "links",
    "keywords",
)
STRING_FIELDS = (
    "name",
    "email",
    "phone",
    "city",
    "linkedin",
    "github",
    "portfolio",
    "summary",
)


class ResumeExtractionResult(BaseModel):
    """Resume profile plus provider and fallback metadata."""

    model_config = ConfigDict(extra="forbid")

    profile: ResumeProfileSchema
    provider: str
    requested_provider: str
    fallback_used: bool = False
    warning: str = ""


def extract_resume_profile(
    resume_text: str,
    *,
    provider: str = "local",
    api_key: str | None = None,
    model: str | None = None,
    generator: AIResumeGenerator | None = None,
) -> ResumeExtractionResult:
    """Extract resume facts, using AI only when explicitly requested."""
    local = parse_resume_text(resume_text)
    if provider != "gemini":
        return ResumeExtractionResult(
            profile=local,
            provider="local",
            requested_provider=provider,
        )
    try:
        ai_profile = (
            generator(resume_text)
            if generator
            else _extract_with_gemini(resume_text, api_key=api_key, model=model)
        )
        return ResumeExtractionResult(
            profile=_merge_profiles(local, ai_profile, resume_text),
            provider="gemini",
            requested_provider="gemini",
        )
    except Exception as exc:
        return ResumeExtractionResult(
            profile=local,
            provider="local",
            requested_provider="gemini",
            fallback_used=True,
            warning=f"Extração Gemini indisponível; parser local mantido. Motivo: {exc}",
        )


def _extract_with_gemini(
    resume_text: str, *, api_key: str | None = None, model: str | None = None
) -> ResumeProfileSchema:
    key = gemini_api_key(api_key)
    if not key:
        raise RuntimeError("GEMINI_API_KEY não configurada.")
    genai = importlib.import_module("google.genai")
    types = importlib.import_module("google.genai.types")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=gemini_model(model),
        contents=(
            "Extraia somente fatos explícitos deste currículo. Não invente, não complete lacunas "
            "e use string/lista vazia quando a informação não existir.\n\n"
            f"CURRÍCULO:\n{resume_text}"
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=_resume_response_schema(),
            temperature=0,
        ),
    )
    payload = response.parsed if response.parsed else response.text
    return (
        ResumeProfileSchema.model_validate(payload)
        if isinstance(payload, dict)
        else ResumeProfileSchema.model_validate_json(payload)
    )


def _resume_response_schema() -> dict[str, object]:
    properties: dict[str, object] = {field: {"type": "string"} for field in STRING_FIELDS}
    properties.update(
        {field: {"type": "array", "items": {"type": "string"}} for field in LIST_FIELDS}
    )
    return {
        "type": "object",
        "properties": properties,
        "required": [*STRING_FIELDS, *LIST_FIELDS],
    }


def _merge_profiles(
    local: ResumeProfileSchema, ai: ResumeProfileSchema, resume_text: str
) -> ResumeProfileSchema:
    updates: dict[str, object] = {
        field: getattr(ai, field) or getattr(local, field) for field in STRING_FIELDS
    }
    for field in LIST_FIELDS:
        updates[field] = list(dict.fromkeys([*getattr(ai, field), *getattr(local, field)]))
    updates["raw_text"] = resume_text.strip()
    updates["source_type"] = "ai_assisted"
    return local.model_copy(update=updates)
