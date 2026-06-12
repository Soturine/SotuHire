"""Future scoring helpers for public exam intelligence.

This is deliberately simple and isolated from the job matching MVP.
"""

from __future__ import annotations

from modules.core.scoring import clamp_score


def calculate_exam_cost_benefit(
    salary_score: int,
    vacancy_score: int,
    time_score: int,
    syllabus_size_score: int,
) -> int:
    """Calculate a future exam cost-benefit score.

    Higher syllabus_size_score means a better situation, not a larger syllabus.
    """
    return clamp_score(
        (salary_score * 0.35)
        + (vacancy_score * 0.25)
        + (time_score * 0.2)
        + (syllabus_size_score * 0.2)
    )
