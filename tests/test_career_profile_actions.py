from modules.profile import (
    CareerProfile,
    edit_career_profile,
    export_career_profile,
    profile_analysis_defaults,
)


def test_career_profile_can_be_applied_edited_and_exported():
    profile = CareerProfile(
        target_roles=["Desenvolvedor Backend"],
        likely_seniority="junior",
        technical_skills=["Python"],
        preferred_modalities=["remote"],
        preferred_locations=["Brasil"],
        target_companies=["Example"],
    )

    defaults = profile_analysis_defaults(profile)
    edited = edit_career_profile(profile, technical_skills=["Python", "FastAPI"])
    exported = export_career_profile(edited)

    assert defaults["search_target_role"] == "Desenvolvedor Backend"
    assert defaults["target_levels"] == ["junior"]
    assert edited.technical_skills == ["Python", "FastAPI"]
    assert '"FastAPI"' in exported
