"""Rank sources according to fit, risk and user intent."""

from __future__ import annotations

from dataclasses import dataclass, field


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
