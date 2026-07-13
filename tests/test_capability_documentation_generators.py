from __future__ import annotations

from copy import deepcopy

from scripts.generate_integration_matrix import DEFAULT_OUTPUT as MATRIX_OUTPUT
from scripts.generate_integration_matrix import render_matrix
from scripts.generate_prompt_catalog import DEFAULT_OUTPUT as PROMPT_OUTPUT
from scripts.generate_prompt_catalog import prompt_rows, render_catalog
from scripts.validate_capabilities import (
    DEFAULT_MANIFEST,
    frontend_routes,
    load_manifest,
    validate_manifest,
)


def test_capability_manifest_matches_openapi_routes_and_files() -> None:
    manifest = load_manifest(DEFAULT_MANIFEST)

    assert validate_manifest(manifest) == []
    assert len(manifest["capabilities"]) >= 15


def test_capability_validator_rejects_unknown_endpoint_and_prompt() -> None:
    manifest = load_manifest(DEFAULT_MANIFEST)
    invalid = deepcopy(manifest)
    capability = invalid["capabilities"][0]
    capability["api_endpoints"] = ["POST /api/v1/does-not-exist"]
    capability["ai_support"]["prompt_ids"] = ["not_registered_v1"]
    known_operations = {
        endpoint for item in manifest["capabilities"] for endpoint in item["api_endpoints"]
    }

    errors = validate_manifest(
        invalid,
        api_operations=known_operations,
        web_routes=frontend_routes(),
        valid_context_purposes={
            item["context_purpose"] for item in manifest["capabilities"] if item["context_purpose"]
        },
        registered_prompt_ids={
            prompt_id
            for item in manifest["capabilities"]
            for prompt_id in item["ai_support"]["prompt_ids"]
        },
    )

    assert any("endpoint ausente no OpenAPI" in error for error in errors)
    assert any("prompt não registrado" in error for error in errors)


def test_integration_matrix_is_deterministic_and_current() -> None:
    manifest = load_manifest(DEFAULT_MANIFEST)
    expected = render_matrix(manifest)

    assert MATRIX_OUTPUT.read_text(encoding="utf-8") == expected
    for required_field in (
        "capability_id",
        "frontend_route",
        "api_endpoints",
        "backend_services",
        "core_modules",
        "stores",
        "profile_integration",
        "context_purpose",
        "ai_support",
        "extension_support",
        "dedupe_strategy",
        "snapshot_support",
        "tests",
        "docs",
        "status",
        "gaps",
        "last_verified_commit",
    ):
        assert f"`{required_field}`" in expected


def test_prompt_catalog_comes_from_registry_and_marks_unconsumed_contracts() -> None:
    rows = prompt_rows()
    expected = render_catalog(rows)
    by_id = {row["prompt_id"]: row for row in rows}

    assert len(rows) == 14
    assert by_id["career_advice_v1"]["status"] == "registrado sem consumidor"
    assert by_id["domain_classification_v1"]["status"] == "implementado sem fluxo integrado"
    assert by_id["match_analysis_evidence_based_v1"]["consumers"]
    assert by_id["resume_extraction_v1"]["schema"].endswith("ResumeExtractionOutput")
    assert PROMPT_OUTPUT.read_text(encoding="utf-8") == expected
