"""Eligibility and diversity filters for calibrated career evidence."""

from __future__ import annotations

from collections import Counter
from typing import TypeVar

from modules.memory.feedback_calibration import NOT_USEFUL_TAG, USEFUL_TAG
from modules.memory.schemas import CareerMemoryItem

DEFAULT_LIMITS_BY_KIND = {
    "project": 2,
    "project_evidence": 2,
    "github_repo": 2,
    "github_profile": 1,
    "portfolio": 2,
    "commit_analysis": 1,
    "readme_analysis": 1,
    "experience": 2,
    "skill": 2,
    "job_analysis": 2,
    "opportunity": 1,
    "preference": 1,
    "education": 1,
    "resume": 1,
    "feedback": 1,
    "tracker_event": 1,
}
ScoreT = TypeVar("ScoreT")


def is_evidence_candidate(item: CareerMemoryItem) -> bool:
    """Exclude calibration-only feedback from evidence cards."""
    return not (
        item.kind == "feedback"
        and ({USEFUL_TAG, NOT_USEFUL_TAG} & {tag.casefold() for tag in item.tags})
    )


def limit_by_kind(
    ranked: list[tuple[CareerMemoryItem, ScoreT]],
    *,
    top_k: int,
    limits: dict[str, int] | None = None,
) -> list[tuple[CareerMemoryItem, ScoreT]]:
    """Keep results diverse by limiting evidence of each memory kind."""
    kind_limits = {**DEFAULT_LIMITS_BY_KIND, **(limits or {})}
    counts: Counter[str] = Counter()
    output: list[tuple[CareerMemoryItem, ScoreT]] = []
    for item, score in ranked:
        if counts[item.kind] >= kind_limits.get(item.kind, top_k):
            continue
        counts[item.kind] += 1
        output.append((item, score))
        if len(output) >= top_k:
            break
    return output
