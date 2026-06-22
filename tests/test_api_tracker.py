from tests.api_test_helpers import api_client_with_tracker


def test_tracker_crud_and_analytics_endpoints_use_temp_store(tmp_path) -> None:
    client = api_client_with_tracker(tmp_path)

    created = client.post(
        "/api/v1/tracker/jobs",
        json={
            "title": "Backend Python",
            "company": "Empresa Ficticia",
            "requirements": ["Python", "Docker"],
            "status": "applied",
            "match_score": 82,
            "ats_score": 74,
            "source_url": "https://linkedin.com/jobs/123",
        },
    )

    assert created.status_code == 200
    job = created.json()["data"]["job"]
    assert job["status"] == "applied"

    updated = client.patch(
        f"/api/v1/tracker/jobs/{job['id']}",
        json={"status": "interview", "notes": "Entrevista tecnica marcada."},
    )

    assert updated.status_code == 200
    assert updated.json()["data"]["job"]["status"] == "interview"

    assert client.get("/api/v1/tracker/jobs").json()["data"]["jobs"][0]["id"] == job["id"]
    assert client.get("/api/v1/tracker/metrics").json()["data"]["total_saved"] == 1
    assert client.get("/api/v1/tracker/requirements").json()["data"]["top_requirements"]
    assert client.get("/api/v1/tracker/funnel").json()["data"]["stages"]
    assert (
        client.get("/api/v1/tracker/sources").json()["data"]["sources"][0]["name"] == "linkedin.com"
    )
