from __future__ import annotations

from pathlib import Path

from tests.api_test_helpers import api_client


def test_authenticated_browser_routes_remain_registered() -> None:
    client = api_client()

    status = client.get("/api/v1/sources/authenticated-browser/status")
    launch = client.post("/api/v1/sources/authenticated-browser/launch", json={})
    collect = client.post("/api/v1/sources/authenticated-browser/collect", json={})

    assert status.status_code == 200
    assert launch.status_code != 404
    assert collect.status_code != 404


def test_forbidden_ethics_doc_was_not_created() -> None:
    assert not Path("docs/ethics/allowed-vs-not-allowed.md").exists()
