"""Keyword suggestion helpers for resume tailoring."""

from __future__ import annotations

from .keyword_helper import suggest_safe_keywords


def suggest_supported_keywords(job_keywords: list[str], evidence_text: str) -> list[str]:
    """Suggest only keywords that appear in the user's evidence text."""
    return suggest_safe_keywords(job_keywords, evidence_text)
