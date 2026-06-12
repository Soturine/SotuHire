from modules.preferences.opportunity_fit import calculate_opportunity_fit
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
    assert calculate_opportunity_fit(job, prefs) < 40
