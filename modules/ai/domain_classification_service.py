"""Service wrapper for AI-assisted domain classification with fallback."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from modules.ai.json_guard import JsonGuardResult, collect_low_confidence_fields, validate_ai_json
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.prompt_registry import PromptRegistry
from modules.ai.schemas.common import StrictSchema
from modules.ai.schemas.domain_classification import DomainClassificationOutput
from modules.ai.structured_analysis import get_provider
from modules.domain_intelligence.domain_classifier import classify_domain


class DomainClassificationServiceResult(StrictSchema):
    """Domain classification plus provider routing metadata."""

    output: DomainClassificationOutput
    provider: str
    requested_provider: str
    fallback_used: bool = False
    warning: str = ""
    low_confidence_fields: list[str] = Field(default_factory=list)


def classify_domain_structured(
    text: str,
    *,
    text_type: str = "job",
    known_context: dict[str, object] | None = None,
    provider: Any | None = None,
    registry: PromptRegistry | None = None,
) -> DomainClassificationServiceResult:
    """Classify domain with AI when available, otherwise use deterministic rules."""
    selected = provider or get_provider()
    requested_provider = getattr(selected, "name", "unknown")
    prompt_registry = registry or default_prompt_registry()
    try:
        spec = prompt_registry.get("domain_classification_v1")
        payload = {
            "text": text,
            "text_type": text_type,
            "known_context": known_context or {},
            "language": "pt-BR",
        }
        result = _coerce_domain_output(selected.generate_structured(spec, payload))
        return DomainClassificationServiceResult(
            output=result.data,
            provider=requested_provider,
            requested_provider=requested_provider,
            low_confidence_fields=result.low_confidence_fields,
        )
    except Exception as exc:
        fallback = classify_domain(text, text_type=text_type, known_context=known_context)
        return DomainClassificationServiceResult(
            output=fallback,
            provider="local",
            requested_provider=requested_provider,
            fallback_used=True,
            warning=f"Structured domain classification unavailable; local rules used. Reason: {exc}",
            low_confidence_fields=collect_low_confidence_fields(fallback.model_dump(mode="json")),
        )


def _coerce_domain_output(payload: Any) -> JsonGuardResult[DomainClassificationOutput]:
    if isinstance(payload, DomainClassificationOutput):
        return JsonGuardResult(
            data=payload,
            low_confidence_fields=collect_low_confidence_fields(payload.model_dump(mode="json")),
        )
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return validate_ai_json(payload, DomainClassificationOutput)
