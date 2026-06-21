"""ATS keyword review powered by Match Engine 2 evidence."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from modules.core.text_utils import normalize_text
from modules.schemas.job_analysis import JobAnalysisSchema


class AtsKeywordReview(BaseModel):
    """Keyword groups separated by evidence safety."""

    model_config = ConfigDict(extra="forbid")

    present: list[str] = Field(default_factory=list)
    missing_but_safe_to_add_if_true: list[str] = Field(default_factory=list)
    missing_without_evidence: list[str] = Field(default_factory=list)


def review_keywords_with_match(
    analysis: JobAnalysisSchema,
    job_keywords: list[str],
) -> AtsKeywordReview:
    """Classify ATS keywords using Match Engine 2 evidence when available."""
    if analysis.analysis_version != "match_engine_v2":
        return AtsKeywordReview(missing_without_evidence=list(dict.fromkeys(job_keywords)))

    matched_corpus = _normalized_set(
        [*analysis.ats_present_keywords, *analysis.matched_requirements, *analysis.evidence_used]
    )
    safe_if_true_corpus = _normalized_set(
        [*analysis.ats_missing_but_safe_to_add, *analysis.partial_requirements]
    )
    unsupported_corpus = _normalized_set(
        [*analysis.ats_missing_without_evidence, *analysis.missing_requirements]
    )

    present: list[str] = []
    safe_if_true: list[str] = []
    unsupported: list[str] = []
    for keyword in job_keywords:
        normalized = normalize_text(keyword)
        if _contains(matched_corpus, normalized):
            present.append(keyword)
        elif _contains(safe_if_true_corpus, normalized):
            safe_if_true.append(keyword)
        elif _contains(unsupported_corpus, normalized):
            unsupported.append(keyword)
        else:
            unsupported.append(keyword)
    return AtsKeywordReview(
        present=list(dict.fromkeys(present)),
        missing_but_safe_to_add_if_true=list(dict.fromkeys(safe_if_true)),
        missing_without_evidence=list(dict.fromkeys(unsupported)),
    )


def _normalized_set(items: list[str]) -> set[str]:
    return {normalize_text(item) for item in items if item.strip()}


def _contains(corpus: set[str], keyword: str) -> bool:
    return any(keyword and (keyword in item or item in keyword) for item in corpus)
