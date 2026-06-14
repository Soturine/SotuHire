"""Deterministic public commit-message analysis."""

from __future__ import annotations

import re

from modules.portfolio.schemas import CommitAnalysis

CONVENTIONAL = re.compile(
    r"^(feat|fix|docs|test|refactor|perf|build|ci|chore|style)(\(.+\))?!?:\s+\S+",
    re.IGNORECASE,
)
GENERIC = {"update", "updates", "fix", "changes", "misc", "test", "wip", "commit"}


def analyze_commits(messages: list[str]) -> CommitAnalysis:
    """Score recent commit messages without requiring network or AI."""
    cleaned = [message.strip() for message in messages if message.strip()][:100]
    if not cleaned:
        return CommitAnalysis(
            commit_quality_score=20,
            maintenance_signal_score=10,
            professionalism_score=20,
            conventional_ratio=0,
            generic_messages=[],
            relevant_messages=[],
        )
    conventional = [message for message in cleaned if CONVENTIONAL.match(message)]
    generic = [message for message in cleaned if message.casefold().strip(".!") in GENERIC]
    relevant = [
        message for message in cleaned if len(message.split()) >= 3 and message not in generic
    ]
    ratio = len(conventional) / len(cleaned)
    quality = _clamp(35 + round(ratio * 40) + len(relevant) * 3 - len(generic) * 8)
    maintenance = _clamp(20 + min(len(cleaned), 20) * 4)
    professionalism = _clamp(35 + round(ratio * 35) + len(relevant) * 2 - len(generic) * 6)
    return CommitAnalysis(
        commit_quality_score=quality,
        maintenance_signal_score=maintenance,
        professionalism_score=professionalism,
        conventional_ratio=round(ratio, 2),
        generic_messages=generic[:10],
        relevant_messages=relevant[:10],
    )


def _clamp(value: int) -> int:
    return max(0, min(100, value))
