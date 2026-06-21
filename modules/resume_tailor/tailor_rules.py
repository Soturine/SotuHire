"""Business rules for safe resume tailoring."""

from __future__ import annotations

from modules.core.text_utils import extract_keywords, first_sentences
from modules.resume_tailor.keyword_helper import suggest_safe_keywords
from modules.resume_tailor.section_ranker import rank_resume_sections
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput, TailoredResumeSection

INDUSTRIAL_TERMS = {
    "embraer",
    "aeroespacial",
    "aeronáutica",
    "aeronautica",
    "industrial",
    "manufatura",
    "engenharia",
    "produção",
    "producao",
    "vale do paraíba",
    "são josé dos campos",
    "sao jose dos campos",
}


def should_emphasize_industrial_background(job_text: str) -> bool:
    """Return True when industrial/aerospace background should be emphasized."""
    normalized = job_text.lower()
    return any(term in normalized for term in INDUSTRIAL_TERMS)


def detect_tailor_warnings(output: ResumeTailorOutput) -> list[str]:
    """Return warnings for unsafe or suspicious tailored output."""
    warnings = list(output.warnings)
    for section in output.tailored_sections:
        if section.invented_information:
            warnings.append(
                f"A seção '{section.section_name}' foi marcada como informação inventada."
            )
        if not section.evidence_source.strip():
            warnings.append(f"A seção '{section.section_name}' não possui fonte de evidência.")
    return warnings


def build_safe_tailor_output(
    target_role: str,
    job_text: str,
    evidence_text: str,
    target_company: str | None = None,
    match_analysis: JobAnalysisSchema | None = None,
) -> ResumeTailorOutput:
    """Build evidence-backed resume suggestions without inventing facts."""
    job_keywords = extract_keywords(job_text)
    safe_keywords = suggest_safe_keywords(job_keywords, evidence_text)
    unsupported = [keyword for keyword in job_keywords if keyword not in safe_keywords]
    available_sections = ["Resumo", "Experiencia", "Projetos", "Skills", "Educacao"]
    warnings = [
        f"Keyword pedida pela vaga sem evidencia suficiente: {keyword}"
        for keyword in unsupported[:10]
    ]
    if match_analysis:
        safe_keywords = _merge_items(safe_keywords, match_analysis.ats_present_keywords)
        warnings.extend(_match_warnings(match_analysis))

    tailored_sections: list[TailoredResumeSection] = []
    evidence_sentences = _merge_items(
        first_sentences(evidence_text, limit=8),
        (match_analysis.evidence_used[:5] if match_analysis else []),
    )
    original_summary = " ".join(evidence_sentences[:2])
    improved_bullets = [_improve_bullet(sentence) for sentence in evidence_sentences[:5]]
    if original_summary:
        tailored_sections.append(
            TailoredResumeSection(
                section_name="Resumo direcionado",
                original_text=original_summary,
                tailored_text=original_summary,
                reason_for_change=(
                    "Preservar apenas evidencias fornecidas; revisar a ordem e o destaque manualmente."
                ),
                evidence_source="curriculo ou evidencia fornecida pelo usuario",
            )
        )
    else:
        warnings.append("Nenhuma evidencia fornecida para criar sugestoes de curriculo.")

    return ResumeTailorOutput(
        target_role=target_role,
        target_company=target_company,
        section_order=rank_resume_sections(job_text, available_sections),
        tailored_sections=tailored_sections,
        professional_summary=original_summary,
        improved_bullets=improved_bullets,
        keywords_added=safe_keywords,
        evidence_used=evidence_sentences[:5],
        warnings=warnings,
    )


def _improve_bullet(text: str) -> str:
    """Normalize an evidence sentence into a reviewable resume bullet."""
    cleaned = text.strip(" -*\t")
    if not cleaned:
        return ""
    improved = cleaned[0].upper() + cleaned[1:]
    return improved if improved.endswith((".", "!", "?")) else f"{improved}."


def _match_warnings(match_analysis: JobAnalysisSchema) -> list[str]:
    warnings = []
    warnings.extend(
        f"Gap critico do Match Engine 2.0: {gap}" for gap in match_analysis.critical_gaps[:5]
    )
    warnings.extend(
        f"Adicionar somente se for verdadeiro e houver evidencia: {keyword}"
        for keyword in match_analysis.ats_missing_but_safe_to_add[:8]
    )
    warnings.extend(
        f"Nao declarar sem evidencia: {keyword}"
        for keyword in match_analysis.ats_missing_without_evidence[:8]
    )
    return warnings


def _merge_items(*groups: list[str]) -> list[str]:
    return list(dict.fromkeys(item for group in groups for item in group if item.strip()))
