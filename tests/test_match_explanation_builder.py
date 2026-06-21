from modules.matching.explanation_builder import build_match_explanation
from modules.matching.models import CandidateEvidence
from modules.matching.requirement_matcher import match_requirement, normalize_requirement
from modules.matching.risk_adjustment import build_critical_gaps
from modules.matching.score_calculator import calculate_match_scores
from modules.matching.transferable_skills import TransferableSkillMatch


def test_explanation_lists_main_reasons_and_safe_actions() -> None:
    fastapi_requirement = normalize_requirement(
        "FastAPI",
        category="hard_skill",
        importance="required",
        criticality="high",
    )
    fastapi_evidence = CandidateEvidence(
        skill="FastAPI",
        normalized_name="FastAPI",
        category="hard_skill",
        evidence_source="github",
        evidence_text="FastAPI em modules/api.py",
        evidence_file="modules/api.py",
        strength="strong",
        confidence=0.9,
    )
    matched = match_requirement(fastapi_requirement, [fastapi_evidence])
    missing_license = match_requirement(
        normalize_requirement("CREA obrigatorio", importance="required"),
        [],
    )
    matches = [matched, missing_license]
    gaps = build_critical_gaps(matches)
    scores = calculate_match_scores(
        matches=matches,
        evidence=[fastapi_evidence],
        transferable_skills=[],
    )

    explanation = build_match_explanation(
        matches=matches,
        critical_gaps=gaps,
        transferable_skills=[
            TransferableSkillMatch(
                original_skill="Arquitetura",
                target_requirement="projeto",
                transfer_level="medium",
                confidence=0.7,
                limitation="nao substitui CREA ativo.",
            )
        ],
        scores=scores,
    )

    assert "Match" in explanation.summary
    assert "FastAPI" in explanation.matched_requirements
    assert any("CREA" in item for item in explanation.critical_gaps)
    assert any("Obrig" in item for item in explanation.score_reasoning)
    assert any("github: FastAPI" in item for item in explanation.evidence_used)
    assert not any("adicione" in item.casefold() for item in explanation.safe_actions)
    assert not any("inclua" in item.casefold() for item in explanation.safe_actions)
