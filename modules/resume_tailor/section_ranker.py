"""Simple section ranking for tailored resumes."""

from __future__ import annotations


def rank_sections(job_text: str, available_sections: list[str]) -> list[str]:
    """Rank resume sections based on the job text using simple deterministic rules."""
    text = job_text.lower()
    scores: dict[str, int] = {section: 0 for section in available_sections}
    for section in available_sections:
        key = section.lower()
        if "project" in key or "projeto" in key:
            scores[section] += 3 if any(term in text for term in ["github", "projeto", "portfolio"]) else 1
        if "skill" in key or "compet" in key:
            scores[section] += 2 if any(term in text for term in ["python", "sql", "java", "qa"]) else 1
        if "educ" in key or "form" in key:
            scores[section] += 2 if any(term in text for term in ["estágio", "trainee", "engenharia"]) else 1
        if "work" in key or "exper" in key:
            scores[section] += 2
    return sorted(available_sections, key=lambda section: scores[section], reverse=True)
