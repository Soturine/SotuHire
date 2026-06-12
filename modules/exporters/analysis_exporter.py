"""Simple JSON and Markdown exports for reviewed analysis data."""

from __future__ import annotations

import re
from pathlib import Path

from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.resume_tailor import ResumeTailorOutput


def analysis_to_json(analysis: JobAnalysisSchema) -> str:
    """Serialize a validated analysis as readable JSON."""
    return analysis.model_dump_json(indent=2)


def _markdown_list(items: list[str], empty: str = "Nenhum item.") -> str:
    return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"


def analysis_to_markdown(analysis: JobAnalysisSchema) -> str:
    """Create a compact Markdown analysis summary."""
    return f"""# Analise SotuHire

## Scores

| Score | Valor |
|---|---:|
| Match | {analysis.match_score} |
| ATS | {analysis.ats_score} |
| Opportunity Fit | {analysis.opportunity_fit_score} |
| Risk | {analysis.risk_score} |

## Recomendacao

`{analysis.recommendation}`

## Pontos fortes

{_markdown_list(analysis.strengths)}

## Gaps

{_markdown_list(analysis.gaps)}

## Keywords ausentes

{_markdown_list(analysis.missing_keywords)}

## Resumo direcionado

{analysis.tailored_summary or "Sem resumo direcionado."}
"""


def tailor_to_markdown(tailor: ResumeTailorOutput) -> str:
    """Create a Markdown document with safe tailoring suggestions."""
    sections = "\n\n".join(
        f"### {section.section_name}\n\n"
        f"**Original:** {section.original_text}\n\n"
        f"**Sugestao:** {section.tailored_text}\n\n"
        f"**Evidencia:** {section.evidence_source}"
        for section in tailor.tailored_sections
    )
    return f"""# Resume Tailor: {tailor.target_role}

## Ordem sugerida

{_markdown_list(tailor.section_order)}

## Resumo profissional direcionado

{tailor.professional_summary or "Sem resumo sugerido."}

## Bullet points melhorados

{_markdown_list(tailor.improved_bullets)}

## Keywords seguras

{_markdown_list(tailor.keywords_added)}

## Evidencias usadas

{_markdown_list(tailor.evidence_used)}

## Sugestoes por secao

{sections or "Nenhuma secao sugerida."}

## Warnings

{_markdown_list(tailor.warnings)}
"""


def save_export(content: str, filename: str, directory: str | Path = "exports") -> Path:
    """Write a non-sensitive export to the configured local directory."""
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", filename).strip("-") or "export.txt"
    target_directory = Path(directory)
    target_directory.mkdir(parents=True, exist_ok=True)
    target = target_directory / safe_name
    target.write_text(content, encoding="utf-8")
    return target
