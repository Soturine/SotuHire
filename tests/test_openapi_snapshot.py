"""The web client's contract test reads a committed OpenAPI copy; it must match the API."""

from __future__ import annotations

import json
from pathlib import Path

from apps.api.main import app

SNAPSHOT = (
    Path(__file__).resolve().parents[1] / "apps" / "web" / "tests" / "contract" / "openapi.json"
)


def test_committed_openapi_matches_the_api() -> None:
    committed = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(app.openapi())), (
        "apps/web/tests/contract/openapi.json is stale: run python scripts/export_openapi.py"
    )
