"""The web client's contract test reads a committed contract view of the OpenAPI; it must match.

The view (scripts/export_openapi.py) keeps request bodies, 2xx response bodies and the schemas
they reach, without titles, descriptions, defaults or FastAPI's own 422 responses: CI installs the
latest compatible FastAPI/Pydantic, which render those differently without changing the API.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

from apps.api.main import app

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "apps" / "web" / "tests" / "contract" / "openapi.json"
_SPEC = importlib.util.spec_from_file_location(
    "export_openapi", ROOT / "scripts" / "export_openapi.py"
)
assert _SPEC and _SPEC.loader
_EXPORT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_EXPORT)
contract_view = _EXPORT.contract_view


def test_committed_contract_view_matches_the_api() -> None:
    committed = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert committed == contract_view(app.openapi()), (
        "apps/web/tests/contract/openapi.json is stale: run python scripts/export_openapi.py"
    )


def _request_schema_name(spec: dict) -> str:
    body = spec["paths"]["/api/v1/tracker/jobs"]["post"]["requestBody"]
    return body["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[-1]


def test_a_new_request_field_changes_the_view() -> None:
    spec = app.openapi()
    changed = copy.deepcopy(spec)
    name = _request_schema_name(changed)
    changed["components"]["schemas"][name]["properties"]["source"] = {"type": "string"}
    assert contract_view(changed) != contract_view(spec)


def test_a_changed_response_field_changes_the_view_and_a_new_title_does_not() -> None:
    spec = app.openapi()
    view = contract_view(spec)
    response_only = next(
        name
        for name, schema in view["components"]["schemas"].items()
        if name.endswith("Response") and schema.get("properties")
    )
    renamed = copy.deepcopy(spec)
    props = renamed["components"]["schemas"][response_only]["properties"]
    first = next(iter(props))
    props[f"{first}_renamed"] = props.pop(first)
    titled = copy.deepcopy(spec)
    titled["components"]["schemas"][response_only]["title"] = "Another title"
    assert contract_view(renamed) != view
    assert contract_view(titled) == view
