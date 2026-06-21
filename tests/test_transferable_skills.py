from modules.core.text_utils import normalize_text
from modules.matching.models import CandidateEvidence
from modules.matching.requirement_matcher import match_requirement, normalize_requirement
from modules.matching.transferable_skills import find_transferable_skills


def test_transferable_skill_supports_but_does_not_become_direct_match() -> None:
    evidence = [
        CandidateEvidence(
            skill="Professor",
            normalized_name="professor",
            category="experience",
            evidence_source="resume",
            evidence_text="Professor com planejamento pedagogico e comunicacao.",
            strength="strong",
            confidence=0.82,
        )
    ]
    requirement = normalize_requirement(
        "treinamento",
        category="hard_skill",
        importance="required",
        criticality="high",
    )

    direct_match = match_requirement(requirement, evidence)
    transferable = find_transferable_skills(evidence, [requirement])

    assert direct_match.match_status == "missing"
    assert transferable
    assert transferable[0].target_requirement == "treinamento"
    assert "nao comprova experiencia corporativa direta" in normalize_text(
        transferable[0].limitation
    )


def test_cybersecurity_transferable_skills_map_risk_and_documentation() -> None:
    evidence = [
        CandidateEvidence(
            skill="Cybersecurity",
            normalized_name="cybersecurity",
            category="domain_knowledge",
            evidence_source="resume",
            evidence_text="Analise de risco, investigacao e documentacao de incidentes.",
            strength="medium",
            confidence=0.8,
        )
    ]
    requirements = [
        normalize_requirement("risco", category="responsibility"),
        normalize_requirement("documentacao", category="responsibility"),
    ]

    transferable = find_transferable_skills(evidence, requirements)

    assert {item.target_requirement for item in transferable} == {"risco", "documentacao"}
