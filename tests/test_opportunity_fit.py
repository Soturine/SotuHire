from modules.preferences.opportunity_fit import (
    calculate_opportunity_fit,
    calculate_opportunity_fit_score,
)
from modules.schemas.user_preferences import UserPreferences


def test_opportunity_fit_rewards_matching_preferences():
    prefs = UserPreferences(
        preferred_locations=["São José dos Campos", "Jacareí"],
        preferred_modalities=["remote", "hybrid"],
        min_salary=1800,
        accepted_contracts=["estágio", "CLT"],
        target_levels=["estágio", "júnior"],
    )
    job = {
        "location": "São José dos Campos",
        "modality": "hybrid",
        "salary_min": 2200,
        "contract": "estágio",
        "seniority": "júnior",
    }
    assert calculate_opportunity_fit(job, prefs) == 100


def test_opportunity_fit_penalizes_senior_onsite_far_job():
    prefs = UserPreferences(
        preferred_locations=["Jacareí"],
        preferred_modalities=["remote"],
        min_salary=2500,
        accepted_contracts=["CLT"],
        target_levels=["júnior"],
    )
    job = {
        "location": "Rio de Janeiro",
        "modality": "onsite",
        "salary_min": 1500,
        "contract": "PJ",
        "seniority": "senior",
    }
    score = calculate_opportunity_fit(job, prefs)

    assert score is not None
    assert score < 40


def test_opportunity_fit_score_is_neutral_without_preferences():
    assert calculate_opportunity_fit_score({}, UserPreferences()) == 70


def test_opportunity_fit_accepts_empty_job_without_breaking():
    prefs = UserPreferences(
        preferred_locations=["São Paulo"],
        preferred_modalities=["remote"],
        min_salary=5000,
    )

    score = calculate_opportunity_fit_score({}, prefs)

    assert 0 <= score <= 100
