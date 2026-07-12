"""Canonical identities shared by profile, memory, opportunities and public records."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from modules.core.text_utils import normalize_text

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "referrer",
    "source",
    "tracking",
    "trk",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}
DOI_PATTERN = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?(10\.\d{4,9}/\S+)", re.I)
ORCID_PATTERN = re.compile(r"(?:https?://orcid\.org/)?(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", re.I)


def normalize_entity_url(url: str) -> str:
    """Remove fragments/tracking while retaining query keys that identify an entity."""
    cleaned = str(url or "").strip()
    if not cleaned:
        return ""
    parts = urlsplit(cleaned)
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key.casefold() not in TRACKING_QUERY_KEYS and not key.casefold().startswith("utm_")
        )
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), path, query, ""))


def normalize_doi(value: str) -> str:
    """Return a lowercase DOI without URL/prefix punctuation."""
    match = DOI_PATTERN.search(str(value or "").strip())
    return match.group(1).rstrip(".,;)").casefold() if match else ""


def normalize_orcid(value: str) -> str:
    """Return a canonical ORCID when present."""
    match = ORCID_PATTERN.search(str(value or "").strip())
    return match.group(1).upper() if match else ""


def normalize_github_repo(value: str) -> str:
    """Return ``owner/repo`` for public GitHub URLs or owner/repo input."""
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    parts = urlsplit(cleaned if "://" in cleaned else f"https://github.com/{cleaned}")
    if parts.netloc.casefold() not in {"github.com", "www.github.com"}:
        return ""
    path_parts = [part for part in parts.path.split("/") if part]
    if len(path_parts) < 2:
        return ""
    return f"{path_parts[0].casefold()}/{path_parts[1].removesuffix('.git').casefold()}"


def content_fingerprint(*parts: str) -> str:
    """Return a stable hash for normalized textual content."""
    content = "\0".join(normalize_text(part) for part in parts if str(part or "").strip())
    return hashlib.sha256(content.encode("utf-8")).hexdigest() if content else ""


def profile_item_identity(
    *, item_type: str, title: str, source: str = "", source_ref: str = "", evidence: str = ""
) -> str:
    """Prefer durable references for a profile item, then use semantic content."""
    reference = _canonical_reference(source_ref)
    if reference:
        return f"profile-ref:{normalize_text(item_type)}:{reference}"
    # Import path and evidence wording frequently differ for the same user-reviewed
    # credential. Keep those fields as provenance, not as part of its identity.
    return "profile:" + content_fingerprint(item_type, title)


def memory_item_identity(
    *, kind: str, title: str, source: str = "", source_ref: str = "", content: str = ""
) -> str:
    """Build a memory identity that links repeated provenance before textual fallback."""
    reference = _canonical_reference(source_ref)
    if reference:
        return f"memory-ref:{normalize_text(kind)}:{reference}"
    return "memory:" + content_fingerprint(kind, title, source, content[:1_000])


def public_exam_identity(
    *,
    source_url: str = "",
    notice_number: str = "",
    organization: str = "",
    exam_board: str = "",
    title: str = "",
    raw_text: str = "",
) -> str:
    """Build a stable edital identity from URL, official number or content."""
    url = normalize_entity_url(source_url)
    if url:
        return f"public-exam-url:{url}"
    if notice_number and organization:
        return "public-exam-number:" + content_fingerprint(notice_number, organization, exam_board)
    return "public-exam-content:" + content_fingerprint(title, organization, raw_text[:2_000])


def project_identity(*, url: str = "", owner: str = "", repo: str = "", title: str = "") -> str:
    """Build a repository/portfolio identity without assuming every project is GitHub."""
    github = normalize_github_repo(url or f"{owner}/{repo}" if owner and repo else url)
    if github:
        return f"github:{github}"
    normalized_url = normalize_entity_url(url)
    if normalized_url:
        return f"project-url:{normalized_url}"
    return "project:" + content_fingerprint(owner, repo, title)


def merge_source_refs(*groups: Iterable[str]) -> list[str]:
    """Merge provenance references in stable order without losing origins."""
    result: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            cleaned = str(value or "").strip()
            key = cleaned.casefold()
            if cleaned and key and key not in seen:
                seen.add(key)
                result.append(cleaned)
    return result


def _canonical_reference(value: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    doi = normalize_doi(cleaned)
    if doi:
        return f"doi:{doi}"
    orcid = normalize_orcid(cleaned)
    if orcid:
        return f"orcid:{orcid}"
    github = normalize_github_repo(cleaned)
    if github:
        return f"github:{github}"
    url = normalize_entity_url(cleaned) if "://" in cleaned else ""
    return f"url:{url}" if url else normalize_text(cleaned)
