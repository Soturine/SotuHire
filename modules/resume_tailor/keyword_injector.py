"""Keyword suggestion helpers for resume tailoring."""

from __future__ import annotations


def suggest_supported_keywords(job_keywords: list[str], evidence_text: str) -> list[str]:
    """Suggest only keywords that appear in the user's evidence text."""
    evidence = evidence_text.lower()
    supported: list[str] = []
    for keyword in job_keywords:
        if keyword.lower() in evidence:
            supported.append(keyword)
    return supported
