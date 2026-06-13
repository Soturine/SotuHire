from modules.ai.providers.gemini_provider import GeminiProvider


def test_structured_payload_uses_supported_json_schema_subset():
    schema = GeminiProvider.structured_response_schema()
    serialized = str(schema)
    properties = schema["properties"]

    assert schema["type"] == "object"
    assert isinstance(properties, dict)
    assert "recommendation" in properties
    assert "additionalProperties" not in serialized
    assert "'title'" not in serialized
    assert "'default'" not in serialized
