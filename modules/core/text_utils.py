"""Small text helpers shared by deterministic MVP rules."""

from __future__ import annotations

import re
import unicodedata

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[+#]+|\.[a-z0-9]+)?")
STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "empresa",
    "esta",
    "este",
    "experiencia",
    "para",
    "por",
    "que",
    "requisitos",
    "ser",
    "sera",
    "sobre",
    "sua",
    "suas",
    "tem",
    "ter",
    "the",
    "uma",
    "vaga",
    "voce",
}


def normalize_text(text: str | None) -> str:
    """Return lowercase, accent-free text with normalized whitespace."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    lowered = ascii_text.lower()
    return " ".join(lowered.split())


def tokenize(text: str | None) -> list[str]:
    """Extract normalized word-like tokens while preserving their order."""
    return TOKEN_PATTERN.findall(normalize_text(text))


def extract_keywords(text: str | None, limit: int = 40) -> list[str]:
    """Extract unique, meaningful keyword candidates from text."""
    keywords: list[str] = []
    seen: set[str] = set()
    for token in tokenize(text):
        if token in STOPWORDS or len(token) < 3 or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= limit:
            break
    return keywords


def keyword_coverage(reference_text: str | None, candidate_text: str | None) -> int:
    """Return candidate coverage of reference keywords as a 0-100 score."""
    reference = extract_keywords(reference_text)
    if not reference:
        return 0
    candidate = set(extract_keywords(candidate_text, limit=200))
    matches = sum(keyword in candidate for keyword in reference)
    return round(matches / len(reference) * 100)


def first_sentences(text: str | None, limit: int = 2) -> list[str]:
    """Return the first non-empty sentences from user-provided text."""
    sentences = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()][:limit]
