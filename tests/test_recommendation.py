from modules.analyzer.recommendation import (
    build_recommendation,
    calculate_risk_score,
    detect_risk_flags,
)


def test_build_recommendation_uses_allowed_values():
    recommendations = {
        build_recommendation(90, 90, 0, 90),
        build_recommendation(60, 60, 10, 60),
        build_recommendation(40, 20, 10, 20),
        build_recommendation(90, 90, 100, 90),
    }

    assert recommendations <= {"apply", "apply_with_adjustments", "save_for_later", "ignore"}


def test_high_risk_forces_ignore():
    assert build_recommendation(100, 100, 100, 100) == "ignore"


def test_detect_risk_flags_accepts_empty_text():
    flags = detect_risk_flags("")

    assert flags == ["Descricao da vaga vazia."]
    assert calculate_risk_score(flags) == 100


def test_detect_risk_flags_spots_seniority_mismatch():
    flags = detect_risk_flags(
        "Buscamos especialista senior para liderar uma plataforma critica com disponibilidade total.",
        "Pessoa desenvolvedora junior com projetos academicos.",
    )

    assert any("Senioridade" in flag for flag in flags)
