"""Small GitHub API client for public repository analysis."""

from __future__ import annotations

import json
import os
import re
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from modules.github_analyzer.exceptions import GitHubApiError, GitHubUrlError
from modules.github_analyzer.repository_models import (
    RepositoryIdentity,
    RepositoryMetadata,
    RepositoryTree,
    RepositoryTreeEntry,
    RepositoryTreeEntryType,
    SelectedRepositoryFile,
)

GITHUB_API_URL = "https://api.github.com"
RAW_GITHUB_URL = "https://raw.githubusercontent.com"
USER_AGENT = "SotuHire-GitHub-Analyzer/2.0"
OWNER_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def parse_github_repository_url(value: str) -> tuple[str, str]:
    """Extract owner/repo from a GitHub URL or shorthand."""
    candidate = value.strip()
    if OWNER_REPO_PATTERN.match(candidate):
        owner, repo = candidate.split("/", 1)
        return owner, _clean_repo_name(repo)

    parsed = urlparse(candidate)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise GitHubUrlError("URL must point to github.com.")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise GitHubUrlError("GitHub URL must include owner and repository.")
    return parts[0], _clean_repo_name(parts[1])


class GitHubClient:
    """Minimal GitHub client using public endpoints and an optional token."""

    def __init__(self, token: str | None = None, *, timeout: int = 15) -> None:
        self.token = token if token is not None else os.getenv("GITHUB_TOKEN", "")
        self.timeout = timeout

    def repository_identity(self, value: str) -> RepositoryIdentity:
        """Build a repository identity from URL or owner/repo shorthand."""
        owner, repo = parse_github_repository_url(value)
        return RepositoryIdentity(owner=owner, name=repo, url=f"https://github.com/{owner}/{repo}")

    def get_metadata(self, owner: str, repo: str) -> RepositoryMetadata:
        """Fetch public repository metadata and language bytes."""
        data = self._get_json(f"{GITHUB_API_URL}/repos/{owner}/{repo}")
        languages = self._safe_get_json(f"{GITHUB_API_URL}/repos/{owner}/{repo}/languages")
        default_branch = str(data.get("default_branch") or "")
        branch_data = (
            self._safe_get_json(f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches/{default_branch}")
            if default_branch
            else {}
        )
        branch_commit = branch_data.get("commit")
        ref_sha = str(branch_commit.get("sha") or "") if isinstance(branch_commit, dict) else ""
        rate_limit = self.rate_limit()
        identity = RepositoryIdentity(
            owner=owner,
            name=repo,
            url=str(data.get("html_url") or f"https://github.com/{owner}/{repo}"),
            default_branch=default_branch,
            ref_sha=ref_sha,
        )
        raw_license = data.get("license")
        license_payload = raw_license if isinstance(raw_license, dict) else {}
        core_limit = _dict_value(rate_limit, "resources", "core")
        return RepositoryMetadata(
            identity=identity,
            description=str(data.get("description") or ""),
            topics=[str(topic) for topic in data.get("topics", []) if topic],
            languages={
                str(language): value
                for language, value in languages.items()
                if isinstance(value, int | float)
            },
            stars=_optional_int(data.get("stargazers_count")),
            forks=_optional_int(data.get("forks_count")),
            license=str(license_payload.get("spdx_id") or license_payload.get("name") or ""),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
            homepage=str(data.get("homepage") or ""),
            archived=bool(data.get("archived", False)),
            fork=bool(data.get("fork", False)),
            rate_limit_remaining=_optional_int(_dict_value(core_limit, "remaining")),
        )

    def get_tree(self, owner: str, repo: str, ref: str) -> RepositoryTree:
        """Fetch a recursive repository tree for a branch or commit SHA."""
        safe_ref = quote(ref, safe="")
        data = self._get_json(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{safe_ref}?recursive=1"
        )
        entries = []
        for item in data.get("tree", []):
            if not isinstance(item, dict):
                continue
            entries.append(
                RepositoryTreeEntry(
                    path=str(item.get("path") or ""),
                    type=_entry_type(item.get("type")),
                    size=_optional_int(item.get("size")),
                    sha=str(item.get("sha") or ""),
                    url=str(item.get("url") or ""),
                )
            )
        return RepositoryTree(entries=entries, truncated=bool(data.get("truncated")), ref=ref)

    def fetch_file(
        self,
        owner: str,
        repo: str,
        ref: str,
        file: SelectedRepositoryFile,
        *,
        max_chars: int = 12_000,
    ) -> SelectedRepositoryFile:
        """Fetch raw content for a selected file, truncating prompt context safely."""
        encoded_path = "/".join(quote(part, safe="") for part in file.path.split("/"))
        url = f"{RAW_GITHUB_URL}/{owner}/{repo}/{quote(ref, safe='')}/{encoded_path}"
        request = Request(url, headers=self._headers(raw=True), method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                raw = response.read(max_chars + 1)
        except (HTTPError, URLError, TimeoutError) as exc:
            raise GitHubApiError(f"Could not fetch raw file: {file.path}") from exc
        text = raw.decode("utf-8", errors="replace")
        return file.model_copy(
            update={
                "content": text[:max_chars],
                "fetched": True,
                "truncated": len(text) > max_chars,
            }
        )

    def rate_limit(self) -> dict[str, object]:
        """Return safe public rate-limit information."""
        return self._safe_get_json(f"{GITHUB_API_URL}/rate_limit")

    def _get_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                payload = response.read()
        except HTTPError as exc:
            raise GitHubApiError(f"GitHub API returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError) as exc:
            raise GitHubApiError("GitHub API request failed.") from exc
        try:
            parsed = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise GitHubApiError("GitHub API returned invalid JSON.") from exc
        return cast(dict[str, Any], parsed if isinstance(parsed, dict) else {})

    def _safe_get_json(self, url: str) -> dict[str, Any]:
        try:
            return self._get_json(url)
        except GitHubApiError:
            return {}

    def _headers(self, *, raw: bool = False) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json" if not raw else "text/plain",
            "User-Agent": USER_AGENT,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


def _clean_repo_name(repo: str) -> str:
    cleaned = repo.removesuffix(".git")
    if not cleaned:
        raise GitHubUrlError("Repository name is empty.")
    return cleaned


def _entry_type(value: object) -> RepositoryTreeEntryType:
    return cast(
        RepositoryTreeEntryType,
        value if value in {"blob", "tree", "commit"} else "unknown",
    )


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _dict_value(payload: object, *keys: str) -> object:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
