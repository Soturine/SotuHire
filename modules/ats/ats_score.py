"""Deterministic, explainable ATS checks for pasted resume text."""

from __future__ import annotations

from modules.core.scoring import clamp_score
from modules.core.text_utils import extract_keywords, normalize_text

SECTION_TERMS = {
    "education",
    "educacao",
    "experiencia",
    "formacao",
    "habilidades",
    "projects",
    "projetos",
    "skills",
    "summary",
    "resumo",
}
FORMAT_RISK_MARKERS = {"│", "┃", "┌", "┐", "└", "┘"}


def analyze_ats_issues(resume_text: str, job_text: str = "") -> list[str]:
    """Return simple ATS issues without depending on an AI provider."""
    if not resume_text.strip():
        return ["Curriculo vazio."]

    normalized_resume = normalize_text(resume_text)
    issues: list[str] = []

    if len(normalized_resume) < 250:
        issues.append("Curriculo muito curto para demonstrar evidencias suficientes.")

    sections_found = sum(term in normalized_resume for term in SECTION_TERMS)
    if sections_found < 2:
        issues.append("Poucas secoes reconheciveis por ATS.")

    if any(marker in resume_text for marker in FORMAT_RISK_MARKERS) or resume_text.count("\t") >= 4:
        issues.append("Formatacao em colunas ou tabelas pode dificultar a leitura por ATS.")

    if job_text.strip():
        job_keywords = extract_keywords(job_text)
        resume_keywords = set(extract_keywords(resume_text, limit=200))
        coverage = sum(keyword in resume_keywords for keyword in job_keywords)
        ratio = coverage / len(job_keywords) if job_keywords else 0
        if ratio < 0.3:
            issues.append("Baixa cobertura das palavras-chave da vaga.")

    return issues


def calculate_simple_ats_score(resume_text: str, job_text: str = "") -> int:
    """Calculate a simple ATS score clamped to the 0-100 range."""
    if not resume_text.strip():
        return 0

    score = 100
    issues = analyze_ats_issues(resume_text, job_text)
    penalties = {
        "Curriculo muito curto para demonstrar evidencias suficientes.": 25,
        "Poucas secoes reconheciveis por ATS.": 20,
        "Formatacao em colunas ou tabelas pode dificultar a leitura por ATS.": 20,
        "Baixa cobertura das palavras-chave da vaga.": 35,
    }
    for issue in issues:
        score -= penalties.get(issue, 10)
    return clamp_score(score) or 0
