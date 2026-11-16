"""Universal search over local data, without depending on accents or case.

The frontend search over screens folds text the same way (``src/lib/search.ts``): NFKD, drop the
combining marks, casefold, and every word of the query must appear. Here the same rule runs over
the person's data: evidence, portfolio, confirmed Profile facts and tracked applications. Sensitive
Profile items are never returned, and nothing is invented: a result is a stored record that
contains every word of the query.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass


def fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def _words(query: str) -> list[str]:
    return [word for word in fold(query).split() if word]


@dataclass(frozen=True)
class SearchHit:
    entity_type: str
    entity_id: str
    title: str
    subtitle: str
    route: str
    review_status: str = ""
    score: int = 0


def score(query: str, title: str, *other: str) -> int:
    """0 when some word is missing; higher when the words sit in the title, highest at its start."""
    words = _words(query)
    if not words:
        return 0
    folded_title = fold(title)
    haystack = " ".join([folded_title, *(fold(text) for text in other)])
    if not all(word in haystack for word in words):
        return 0
    if folded_title.startswith(words[0]):
        return 100
    if all(word in folded_title for word in words):
        return 60
    return 20


def rank(query: str, candidates: Iterable[tuple[SearchHit, tuple[str, ...]]], limit: int):
    """Keep candidates that match, best first, stable for ties; at most ``limit``."""
    scored = []
    for order, (hit, extra) in enumerate(candidates):
        value = score(query, hit.title, hit.subtitle, *extra)
        if value:
            scored.append((-value, order, hit))
    scored.sort(key=lambda row: (row[0], row[1]))
    return [SearchHit(**{**hit.__dict__, "score": -value}) for value, _order, hit in scored[:limit]]


__all__ = ["SearchHit", "fold", "rank", "score"]
