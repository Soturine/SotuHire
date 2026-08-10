"""Deterministic interview preparation that never invents candidate answers."""

from __future__ import annotations

import hashlib
import json

from modules.interviews.models import InterviewPreparation, InterviewSession


def prepare_interview_local(
    session: InterviewSession,
    *,
    opportunity_summary: str,
    requirements: list[str],
    confirmed_evidence: list[dict[str, str]],
) -> InterviewPreparation:
    """Build questions and coverage only from explicitly confirmed evidence."""
    evidence_text = " ".join(
        " ".join(str(value) for value in item.values()) for item in confirmed_evidence
    ).casefold()
    strengths: list[str] = []
    gaps: list[str] = []
    evidence_refs: list[str] = []
    for requirement in requirements:
        tokens = [token for token in requirement.casefold().split() if len(token) >= 4]
        if tokens and any(token in evidence_text for token in tokens):
            strengths.append(requirement)
        else:
            gaps.append(requirement)
    for item in confirmed_evidence:
        reference = str(item.get("source_ref", "")).strip()
        if reference:
            evidence_refs.append(reference)
    technical = (
        [f"Como voce aplicou {item}? Cite apenas exemplos confirmados." for item in strengths[:5]]
        if session.interview_type in {"technical", "case", "panel"}
        else []
    )
    behavioral = [
        "Conte uma situacao confirmada em que precisou priorizar trabalho.",
        "Descreva um conflito real e o que aprendeu com ele.",
    ]
    likely = [
        f"Qual evidencia confirma sua experiencia com {requirement}?"
        for requirement in requirements[:8]
    ]
    dependency = hashlib.sha256(
        json.dumps(
            {
                "session": session.model_dump(mode="json"),
                "summary": opportunity_summary,
                "requirements": requirements,
                "evidence": confirmed_evidence,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return InterviewPreparation(
        session_id=session.session_id,
        opportunity_summary=opportunity_summary[:10_000],
        critical_requirements=requirements[:30],
        confirmed_strengths=strengths,
        gaps=gaps,
        likely_questions=likely,
        technical_questions=technical,
        behavioral_questions=behavioral,
        candidate_questions=[
            "Como o sucesso desta funcao e avaliado nos primeiros meses?",
            "Quais sao as prioridades atuais da equipe?",
        ],
        needs_confirmation=gaps,
        evidence_refs=list(dict.fromkeys(evidence_refs)),
        dependency_hash=dependency,
    )


__all__ = ["prepare_interview_local"]
