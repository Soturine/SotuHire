"""Optional Gemini enhancement for deterministic project reports."""

from __future__ import annotations

import importlib

from pydantic import BaseModel, ConfigDict, Field

from modules.ai.setup import gemini_api_key, gemini_model
from modules.portfolio.schemas import ProjectAnalysisPayload, ProjectAnalysisReport


class ProjectAIEnhancement(BaseModel):
    """Small safe subset Gemini may refine without changing deterministic scores."""

    model_config = ConfigDict(extra="forbid")

    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    priority_recommendations: list[str] = Field(default_factory=list)
    resume_highlights: list[str] = Field(default_factory=list)


def enhance_project_report(
    payload: ProjectAnalysisPayload,
    report: ProjectAnalysisReport,
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> ProjectAnalysisReport:
    """Ask Gemini to refine prose while preserving locally calculated scores."""
    key = gemini_api_key(api_key)
    if not key:
        return report
    try:
        genai = importlib.import_module("google.genai")
        types = importlib.import_module("google.genai.types")
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=gemini_model(model),
            contents=(
                "Aprimore somente o texto deste relatório de projeto público. Não invente fatos, "
                "tecnologias, resultados ou experiência. Preserve os scores locais.\n\n"
                f"DADOS CAPTURADOS:\n{payload.model_dump_json()}\n\n"
                f"RELATÓRIO LOCAL:\n{report.model_dump_json()}"
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=ProjectAIEnhancement.model_json_schema(),
                temperature=0,
            ),
        )
        enhancement = (
            ProjectAIEnhancement.model_validate(response.parsed)
            if response.parsed
            else ProjectAIEnhancement.model_validate_json(response.text)
        )
    except Exception:
        return report
    return report.model_copy(
        update={
            "provider_used": "gemini",
            "summary": enhancement.summary or report.summary,
            "strengths": enhancement.strengths or report.strengths,
            "weaknesses": enhancement.weaknesses or report.weaknesses,
            "priority_recommendations": enhancement.priority_recommendations
            or report.priority_recommendations,
            "resume_highlights": enhancement.resume_highlights or report.resume_highlights,
        }
    )
