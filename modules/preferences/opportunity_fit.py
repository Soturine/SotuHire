"""Deterministic Opportunity Fit scoring.

The goal is not to replace AI, but to make user preferences testable and explainable.
"""

from __future__ import annotations

from modules.core.scoring import clamp_score, weighted_score
from modules.schemas.user_preferences import UserPreferences


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def modality_score(job_modality: str | None, preferences: UserPreferences) -> int | None:
    if not preferences.preferred_modalities:
        return None
    modality = _norm(job_modality)
    if not modality:
        return 60
    return 100 if modality in preferences.preferred_modalities else 25


def location_score(job_location: str | None, preferences: UserPreferences) -> int | None:
    if not preferences.preferred_locations:
        return None
    location = _norm(job_location)
    if not location:
        return 60
    preferred = [_norm(item) for item in preferences.preferred_locations]
    return 100 if any(item in location for item in preferred) else 35


def salary_score(job_salary_min: int | None, preferences: UserPreferences) -> int | None:
    if preferences.min_salary is None:
        return None
    if job_salary_min is None:
        return 60
    if job_salary_min >= preferences.min_salary:
        return 100
    ratio = job_salary_min / max(preferences.min_salary, 1)
    return clamp_score(ratio * 100)


def contract_score(job_contract: str | None, preferences: UserPreferences) -> int | None:
    if not preferences.accepted_contracts:
        return None
    contract = _norm(job_contract)
    if not contract:
        return 60
    accepted = [_norm(item) for item in preferences.accepted_contracts]
    return 100 if any(item in contract for item in accepted) else 30


def seniority_score(job_level: str | None, preferences: UserPreferences) -> int | None:
    if not preferences.target_levels:
        return None
    level = _norm(job_level)
    if not level:
        return 60
    targets = [_norm(item) for item in preferences.target_levels]
    if any(item in level for item in targets):
        return 100
    if "senior" in level or "sênior" in level or "lead" in level:
        return 5
    return 45


def calculate_opportunity_fit(job: dict, preferences: UserPreferences) -> int | None:
    """Calculate a weighted fit score from a normalized job dict."""
    values = {
        "modality": modality_score(job.get("modality"), preferences),
        "location": location_score(job.get("location"), preferences),
        "salary": salary_score(job.get("salary_min"), preferences),
        "contract": contract_score(job.get("contract"), preferences),
        "seniority": seniority_score(job.get("seniority"), preferences),
    }
    weights = {
        "modality": preferences.modality_weight,
        "location": preferences.location_weight,
        "salary": preferences.salary_weight,
        "contract": preferences.contract_weight,
        "seniority": preferences.seniority_weight,
    }
    return weighted_score(values, weights)
