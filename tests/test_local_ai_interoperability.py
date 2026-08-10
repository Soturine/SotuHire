from __future__ import annotations

import pytest
from modules.ai.local_interop import local_ai_health, validate_local_ai_endpoint
from modules.ai.provider_routing import provider_task_matrix


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://example.com:11434/v1",
        "http://127.0.0.1:11434/v1?scan=1",
        "http://user:secret@127.0.0.1:11434/v1",
        "file:///tmp/model",
    ],
)
def test_local_ai_default_boundary_rejects_remote_or_ambiguous_endpoints(endpoint: str) -> None:
    with pytest.raises(ValueError):
        validate_local_ai_endpoint("ollama", endpoint)


def test_remote_custom_requires_both_opt_in_and_https(monkeypatch) -> None:
    with pytest.raises(ValueError, match="opt-in"):
        validate_local_ai_endpoint("openai_compatible", "https://models.example/v1")
    with pytest.raises(ValueError, match="HTTPS"):
        validate_local_ai_endpoint(
            "openai_compatible",
            "http://models.example/v1",
            advanced_remote_opt_in=True,
        )
    monkeypatch.setattr(
        "modules.ai.local_interop.validate_public_url",
        lambda value, resolve: None,
    )
    endpoint = validate_local_ai_endpoint(
        "openai_compatible",
        "https://models.example/v1",
        advanced_remote_opt_in=True,
    )
    assert endpoint.remote


def test_health_checks_only_explicit_endpoint_and_lists_models(monkeypatch) -> None:
    seen = []

    def fake_request(endpoint, path, **kwargs):
        seen.append((endpoint.base_url, path))
        return {"data": [{"id": "fixture-model", "owned_by": "local"}]}

    monkeypatch.setattr("modules.ai.local_interop._request_json", fake_request)
    health = local_ai_health("lm_studio", "http://127.0.0.1:1234/v1")
    assert health.status == "ready"
    assert [model.id for model in health.models] == ["fixture-model"]
    assert seen == [("http://127.0.0.1:1234/v1", "/models")]


def test_every_ai_task_has_explicit_local_server_routing_state() -> None:
    matrix = provider_task_matrix()
    assert len(matrix) == 25
    for route in matrix:
        assert set(route.providers) == {
            "local_deterministic",
            "gemini",
            "openai",
            "ollama",
            "lm_studio",
            "openai_compatible",
        }
        assert route.consumer != "registry consumer not documented"
