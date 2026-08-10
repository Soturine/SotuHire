from __future__ import annotations

from modules.taxonomy import taxonomy_content_sha256
from tests.api_test_helpers import api_client


def test_opportunity_observations_and_rankings_use_sqlite_truth(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    candidate = {
        "source": "greenhouse-fixture",
        "source_kind": "greenhouse",
        "source_url": "https://boards.greenhouse.io/example/jobs/123",
        "external_id": "123",
        "title": "Pessoa Engenheira Python",
        "organization": "Empresa Ficticia",
        "location": "Remoto",
        "description": "Python, FastAPI e SQL.",
        "remote": True,
        "source_refs": ["fixture://greenhouse/123"],
    }

    saved = client.post("/api/v1/opportunities/observations", json=candidate)
    ranked = client.post(
        "/api/v1/opportunities/rankings",
        json={
            "candidates": [candidate],
            "profile_id": "profile-fixture",
            "preferences": {
                "target_titles": ["Engenheira Python"],
                "skills": ["Python", "FastAPI"],
                "remote_preferred": True,
            },
        },
    )
    candidates = client.get("/api/v1/opportunities/candidates")
    persisted_rankings = client.get(
        "/api/v1/opportunities/rankings", params={"profile_id": "profile-fixture"}
    )

    assert saved.status_code == ranked.status_code == 201
    assert candidates.status_code == persisted_rankings.status_code == 200
    assert candidates.json()["data"][0]["external_id"] == "123"
    result = persisted_rankings.json()["data"][0]["rank"]
    assert result["fit_score"] > 0
    assert 0 <= result["confidence"] <= 1
    assert 0 <= result["evidence_coverage"] <= 1


def test_taxonomy_dataset_integrity_and_mapping_review(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    records = [{"code": "fixture-1", "title": "Ocupacao Ficticia"}]
    manifest = {
        "system": "cbo",
        "version": "fixture-1",
        "source_url": "https://www.gov.br/trabalho-e-emprego/fixture",
        "license_name": "Fixture baseada em fonte oficial",
        "content_sha256": taxonomy_content_sha256(records),
    }
    dataset = client.post(
        "/api/v1/taxonomy/datasets", json={"manifest": manifest, "records": records}
    )
    mapping = client.post(
        "/api/v1/taxonomy/mappings",
        json={
            "mapping_id": "mapping-fixture",
            "source_text": "Data Engineer",
            "target_id": "occupation-fixture",
            "target_label": "Pessoa Engenheira de Dados",
            "taxonomy_ref": "cbo:fixture",
            "match_method": "semantic_candidate",
            "confidence": 0.82,
        },
    )
    reviewed = client.patch(
        "/api/v1/taxonomy/mappings/mapping-fixture/review",
        json={"review_status": "confirmed"},
    )

    assert dataset.status_code == mapping.status_code == 201
    assert reviewed.status_code == 200
    assert mapping.json()["data"]["review_status"] == "candidate"
    assert reviewed.json()["data"]["review_status"] == "confirmed"
    assert reviewed.json()["data"]["reviewed_at"]
    assert (tmp_path / "sotuhire.db").is_file()
    assert list((tmp_path / "taxonomies" / "cbo" / "fixture-1").glob("*.json"))
