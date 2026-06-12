"""Evidence-backed keyword suggestions for safe resume tailoring."""

from __future__ import annotations

from modules.core.text_utils import extract_keywords, normalize_text


def suggest_safe_keywords(job_text_or_keywords: str | list[str], evidence_text: str) -> list[str]:
    """Suggest only job keywords that already exist in supplied evidence."""
    if isinstance(job_text_or_keywords, str):
        job_keywords = extract_keywords(job_text_or_keywords)
    else:
        job_keywords = job_text_or_keywords

    evidence = normalize_text(evidence_text)
    evidence_keywords = set(extract_keywords(evidence_text, limit=500))
    suggestions: list[str] = []
    for keyword in job_keywords:
        normalized_keyword = normalize_text(keyword)
        is_supported = (
            normalized_keyword in evidence
            if " " in normalized_keyword
            else normalized_keyword in evidence_keywords
        )
        if is_supported and keyword not in suggestions:
            suggestions.append(keyword)
    return suggestions
