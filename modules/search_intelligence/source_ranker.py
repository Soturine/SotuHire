"""Rank sources according to fit, risk and user intent."""

from __future__ import annotations

from dataclasses import dataclass, field

from modules.core.schemas import JobSearchQuery


@dataclass(slots=True)
class SourceProfile:
    name: str
    url: str
    priority: str
    best_for: list[str] = field(default_factory=list)
    risk_level: str = "medium"
    access_modes: list[str] = field(default_factory=list)


DEFAULT_SOURCES: list[SourceProfile] = [
    SourceProfile(
        "MeuHome",
        "https://www.meuhome.com.br/",
        "high",
        ["remote", "hybrid", "tech", "data", "junior", "internship"],
        "low",
        ["manual", "public_page"],
    ),
    SourceProfile(
        "Remotar",
        "https://remotar.com.br/",
        "high",
        ["remote", "brazil"],
        "low",
        ["manual", "public_page"],
    ),
    SourceProfile(
        "Gupy",
        "https://www.gupy.io/",
        "high",
        ["brazil", "internship", "junior", "corporate"],
        "medium",
        ["manual", "public_page"],
    ),
    SourceProfile(
        "CIEE",
        "https://portal.ciee.org.br/",
        "high",
        ["internship", "apprentice", "brazil"],
        "medium",
        ["manual", "public_page"],
    ),
    SourceProfile(
        "Wellfound",
        "https://wellfound.com/jobs",
        "medium",
        ["startup", "remote", "tech"],
        "medium",
        ["manual"],
    ),
]


def rank_sources(
    query: JobSearchQuery, sources: list[SourceProfile] | None = None
) -> list[SourceProfile]:
    """Return sources sorted by simple deterministic fit."""
    pool = sources or DEFAULT_SOURCES
    tokens = {
        query.seniority.value,
        query.modality or "",
        query.location or "",
        *[s.lower() for s in query.skills],
    }

    def score(source: SourceProfile) -> tuple[int, str]:
        fit = sum(1 for tag in source.best_for if tag.lower() in tokens)
        priority = {"high": 3, "medium": 2, "low": 1}.get(source.priority, 0)
        risk_penalty = {"low": 0, "medium": -1, "high": -3}.get(source.risk_level, -1)
        return (fit + priority + risk_penalty, source.name)

    return sorted(pool, key=score, reverse=True)
