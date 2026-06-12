"""Parser placeholder for Currículo Lattes exports/text."""

from __future__ import annotations


def extract_lattes_keywords(text: str) -> list[str]:
    """Extract simple academic keywords from Lattes-like text."""
    candidates = [
        "publicação",
        "projeto",
        "iniciação científica",
        "evento",
        "orientação",
        "pesquisa",
    ]
    normalized = text.lower()
    return [item for item in candidates if item in normalized]
