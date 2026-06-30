from tests.api_test_helpers import api_client


def test_github_repo_analyze_uses_fallback_payload_without_network_dependency() -> None:
    client = api_client()

    response = client.post(
        "/api/v1/github/repo/analyze",
        json={
            "repo_url": "not-a-github-url",
            "fallback_payload": {
                "url": "https://github.com/example/fictitious-api",
                "owner": "example",
                "repo": "fictitious-api",
                "title": "Fictitious API",
                "page_type": "github_repo",
                "visible_text": "FastAPI project with README and tests.",
                "readme_text": "# Fictitious API\nFastAPI project.",
                "files_sampled": ["README.md", "pyproject.toml", "tests/test_api.py"],
                "languages": ["Python"],
                "topics": ["api", "career"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    report = payload["data"]["report"]
    assert report["repository_identity"]["name"] == "fictitious-api"
    assert report["fallback_used"] is True
    assert payload["data"]["profile_evidence_candidates"]
    assert payload["data"]["profile_evidence_candidates"][0]["metadata"]["review_required"] is True
    assert payload["warnings"] == ["Analise GitHub usou fallback local."]
