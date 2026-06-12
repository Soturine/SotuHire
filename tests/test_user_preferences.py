import pytest
from modules.schemas.user_preferences import UserPreferences
from pydantic import ValidationError


def test_user_preferences_accept_valid_values():
    preferences = UserPreferences(
        preferred_locations=["São Paulo"],
        preferred_modalities=["remote", "hybrid"],
        min_salary=5000,
        accepted_contracts=["CLT"],
        target_levels=["junior"],
    )

    assert preferences.has_preferences()


def test_user_preferences_reject_negative_salary():
    with pytest.raises(ValidationError):
        UserPreferences(min_salary=-1)


def test_user_preferences_reject_unknown_modality():
    with pytest.raises(ValidationError):
        UserPreferences.model_validate({"preferred_modalities": ["flexible"]})


def test_empty_user_preferences_are_valid():
    preferences = UserPreferences()

    assert not preferences.has_preferences()
