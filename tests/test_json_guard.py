import pytest
from modules.ai.exceptions import AIJsonParseError, AISchemaValidationError
from modules.ai.json_guard import clean_json_text, validate_ai_json
from pydantic import BaseModel, Field


class GuardSample(BaseModel):
    name: str
    confidence: float = Field(ge=0, le=1)


def test_json_guard_accepts_valid_json() -> None:
    result = validate_ai_json('{"name": "COREN", "confidence": 0.91}', GuardSample)

    assert result.data.name == "COREN"
    assert result.low_confidence_fields == []


def test_json_guard_strips_markdown_fence() -> None:
    raw = """```json
{"name": "BNCC", "confidence": 0.5}
```"""

    result = validate_ai_json(raw, GuardSample)

    assert clean_json_text(raw).startswith("{")
    assert result.data.name == "BNCC"
    assert result.low_confidence_fields == ["$"]


def test_json_guard_rejects_invalid_json_with_clear_error() -> None:
    with pytest.raises(AIJsonParseError, match="Invalid AI JSON response"):
        validate_ai_json("{not-json", GuardSample)


def test_json_guard_rejects_schema_errors() -> None:
    with pytest.raises(AISchemaValidationError, match="GuardSample"):
        validate_ai_json('{"name": "CRP", "confidence": 1.5}', GuardSample)
