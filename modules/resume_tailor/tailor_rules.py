"""Business rules for safe resume tailoring."""

from __future__ import annotations

from modules.schemas.resume_tailor import ResumeTailorOutput

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
