"""Recommendation helper for job analysis."""

from __future__ import annotations

from typing import Literal

from modules.core.scoring import clamp_score
from modules.core.text_utils import normalize_text

Recommendation = Literal["apply", "apply_with_adjustments", "save_for_later", "ignore"]


def detect_risk_flags(job_text: str, resume_text: str = "") -> list[str]:
    """Detect a small set of explainable risk signals in a job description."""
    normalized_job = normalize_text(job_text)
    normalized_resume = normalize_text(resume_text)
    if not normalized_job:
        return ["Descricao da vaga vazia."]

    flags: list[str] = []
    if len(normalized_job) < 120:
        flags.append("Descricao da vaga curta ou vaga.")
    if any(term in normalized_job for term in ["sem remuneracao", "nao remunerado", "voluntario"]):
        flags.append("Possivel oportunidade sem remuneracao.")
    if any(term in normalized_job for term in ["comissao apenas", "somente comissao"]):
        flags.append("Remuneracao possivelmente baseada apenas em comissao.")
    if any(term in normalized_job for term in ["senior", "lead", "especialista"]) and not any(
        term in normalized_resume for term in ["senior", "lead", "especialista"]
    ):
        flags.append("Senioridade da vaga pode estar acima das evidencias do curriculo.")
    return flags


def calculate_risk_score(risk_flags: list[str]) -> int:
    """Convert risk flags to a clamped score."""
    if "Descricao da vaga vazia." in risk_flags:
        return 100
    return clamp_score(len(risk_flags) * 25) or 0


def build_recommendation(
    match_score: int,
    opportunity_fit_score: int,
    risk_score: int,
    ats_score: int = 100,
) -> Recommendation:
    """Choose a recommendation from deterministic, clamped scores."""
    match = clamp_score(match_score) or 0
    fit = clamp_score(opportunity_fit_score) or 0
    risk = clamp_score(risk_score) or 0
    ats = clamp_score(ats_score) or 0

    if risk >= 75:
        return "ignore"
    if match >= 75 and fit >= 65 and ats >= 65:
        return "apply"
    if match >= 55 and fit >= 50 and ats >= 45:
        return "apply_with_adjustments"
    if match >= 35 or fit >= 50:
        return "save_for_later"
    return "ignore"


def choose_recommendation(
    match_score: int, opportunity_fit_score: int, risk_score: int
) -> Recommendation:
    """Backward-compatible recommendation helper."""
    return build_recommendation(match_score, opportunity_fit_score, risk_score)
