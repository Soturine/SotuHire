from modules.memory import CareerMemoryItem
from modules.profile import build_career_profile, infer_preferences, profile_completeness_score
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.user_preferences import UserPreferences


def test_career_profile_is_built_from_resume_memory_and_preferences():
    resume = ResumeProfileSchema(
        skills=["Python", "SQL"],
        soft_skills=["Comunicação"],
        experiences=["Analista júnior em indústria"],
        projects=["API FastAPI"],
        education=["Engenharia"],
        links=["github.com/example"],
    )
    items = [
        CareerMemoryItem(
            kind="job_analysis",
            title="Análise: Desenvolvedor Backend Júnior · Example",
            content="Fortes: Python. Gaps: Docker, AWS.",
            source="analysis",
            tags=["Python", "FastAPI", "apply"],
        ),
        CareerMemoryItem(
            kind="preference",
            title="Modalidades preferidas",
            content="remote",
            source="user_preferences",
            tags=["remote"],
        ),
    ]

    profile = build_career_profile(
        resume,
        items,
        UserPreferences(preferred_locations=["São José dos Campos"]),
    )

    assert "Python" in profile.technical_skills
    assert "Desenvolvedor Backend Júnior" in profile.target_roles
    assert "remote" in profile.preferred_modalities
    assert "Docker" in profile.recurring_gaps
    assert profile.target_companies == ["Example"]
    assert profile_completeness_score(profile) >= 80


def test_preferences_are_inferred_from_history():
    inferred = infer_preferences(
        [
            CareerMemoryItem(
                kind="tracker_event",
                title="Análise: Analista de Dados Júnior · Data Co",
                content="Status applied remote CLT junior",
                source="tracker",
                tags=["Python", "SQL"],
            )
        ]
    )

    assert inferred.target_roles == ["Analista de Dados Júnior"]
    assert "remote" in inferred.modalities
    assert "clt" in inferred.contracts
    assert "Python" in inferred.relevant_skills


def test_empty_career_profile_has_zero_completeness():
    assert profile_completeness_score(build_career_profile(ResumeProfileSchema(), [])) == 0
