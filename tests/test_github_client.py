import pytest
from modules.github_analyzer.exceptions import GitHubUrlError
from modules.github_analyzer.github_client import GitHubClient, parse_github_repository_url


def test_parse_github_repository_url_accepts_url_and_shorthand() -> None:
    assert parse_github_repository_url("https://github.com/Soturine/SotuHire") == (
        "Soturine",
        "SotuHire",
    )
    assert parse_github_repository_url("Soturine/SotuHire.git") == ("Soturine", "SotuHire")


def test_parse_github_repository_url_rejects_non_github_url() -> None:
    with pytest.raises(GitHubUrlError):
        parse_github_repository_url("https://example.com/Soturine/SotuHire")


def test_github_client_uses_optional_token_without_exposing_it() -> None:
    client = GitHubClient(token="secret-token")

    headers = client._headers()  # noqa: SLF001 - verifying safety of request headers

    assert headers["Authorization"] == "Bearer secret-token"
    assert "secret-token" not in repr(client.repository_identity("Soturine/SotuHire"))
