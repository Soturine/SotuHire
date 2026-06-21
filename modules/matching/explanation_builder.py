"""Human-facing explanations for Match Engine 2."""

from __future__ import annotations

from modules.matching.models import (
    CriticalGap,
    MatchExplanation,
    MatchScoreBreakdown,
    RequirementMatch,
    TransferableSkillMatch,
)


def build_match_explanation(
    *,
    matches: list[RequirementMatch],
    critical_gaps: list[CriticalGap],
    transferable_skills: list[TransferableSkillMatch],
    scores: MatchScoreBreakdown,
) -> MatchExplanation:
    """Build a clear explanation for the candidate."""
    matched = [item for item in matches if item.match_status == "matched"]
    partial = [item for item in matches if item.match_status == "partial"]
    missing = [item for item in matches if item.match_status == "missing"]
    return MatchExplanation(
        summary=_summary(scores, critical_gaps),
        score_reasoning=[
            f"Obrigatórios: {scores.required_requirements_score}/100.",
            f"Desejáveis: {scores.preferred_requirements_score}/100.",
            f"Evidências: {scores.evidence_strength_score}/100.",
            f"Penalidade de risco: {scores.risk_penalty}/100.",
            f"Confiança: {scores.confidence_score:.2f}.",
        ],
        matched_requirements=[_req(item) for item in matched],
        partial_requirements=[_req(item) for item in partial],
        missing_requirements=[_req(item) for item in missing],
        critical_gaps=[gap.reason for gap in critical_gaps],
        transferable_skills=[
            (
                f"{item.original_skill} ajuda em {item.target_requirement} "
                f"({item.transfer_level}), mas {item.limitation}"
            )
            for item in transferable_skills
        ],
        evidence_used=[
            f"{evidence.evidence_source}: {evidence.skill}"
            for match in matches
            for evidence in match.candidate_evidence[:2]
        ],
        safe_actions=_safe_actions(matches, critical_gaps),
        resume_improvements=_resume_improvements(matches),
        portfolio_github_improvements=_portfolio_improvements(scores),
    )


def _summary(scores: MatchScoreBreakdown, gaps: list[CriticalGap]) -> str:
    if any(gap.severity == "knockout" for gap in gaps):
        return (
            f"Match {scores.overall_score}/100 com gap crítico. "
            "Revise requisitos obrigatórios antes de aplicar."
        )
    if scores.overall_score >= 75:
        return f"Match {scores.overall_score}/100 com boa compatibilidade e evidências úteis."
    if scores.overall_score >= 55:
        return (
            f"Match {scores.overall_score}/100 com compatibilidade parcial e ajustes necessários."
        )
    return f"Match {scores.overall_score}/100 baixo ou incerto para esta vaga."


def _safe_actions(matches: list[RequirementMatch], gaps: list[CriticalGap]) -> list[str]:
    actions = [gap.safe_action for gap in gaps]
    actions.extend(match.safe_action for match in matches if match.match_status == "partial")
    if not actions:
        actions.append("Manter evidências verdadeiras visíveis e adaptar o currículo à vaga.")
    return list(dict.fromkeys(actions))[:8]


def _resume_improvements(matches: list[RequirementMatch]) -> list[str]:
    improvements = []
    for match in matches:
        if match.match_status in {"missing", "partial"}:
            improvements.append(
                f"Se for verdadeiro, tornar mais visível: {match.requirement.requirement_text}."
            )
    return improvements[:8]


def _portfolio_improvements(scores: MatchScoreBreakdown) -> list[str]:
    if scores.portfolio_github_evidence_score >= 60:
        return ["Usar GitHub/portfólio como evidência complementar no currículo e entrevista."]
    return ["Adicionar evidências reais no GitHub/portfólio quando elas existirem."]


def _req(match: RequirementMatch) -> str:
    return match.requirement.requirement_text or match.requirement.normalized_name
