"""Configurable and explainable scoring for local career memory."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from modules.core.text_utils import extract_keywords, normalize_text
from modules.memory.feedback_calibration import evidence_feedback_adjustment, outcome_adjustment
from modules.memory.schemas import CareerMemoryItem

KIND_BOOSTS = {
    "skill": 0.16,
    "project": 0.14,
    "experience": 0.14,
    "preference": 0.1,
    "job_analysis": 0.08,
    "opportunity": 0.06,
    "resume": 0.04,
    "education": 0.03,
    "feedback": 0.02,
    "tracker_event": 0.02,
}
GENERIC_TITLES = {"vaga", "oportunidade", "resumo profissional", "analise", "feedback"}


class MemoryScoringWeights(BaseModel):
    """Tunable deterministic weights for local retrieval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    keyword_overlap: float = 0.5
    tag_overlap: float = 0.2
    phrase_boost: float = 0.1
    recency_boost: float = 0.1
    generic_penalty: float = 0.14
    stale_penalty: float = 0.12
    kind_boosts: dict[str, float] = Field(default_factory=lambda: dict(KIND_BOOSTS))


class MemoryScore(BaseModel):
    """Transparent final score and its deterministic components."""

    model_config = ConfigDict(extra="forbid")

    final_score: float = Field(ge=0.0, le=1.0)
    components: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)


def _generic_penalty(item: CareerMemoryItem, content_tokens: set[str], weight: float) -> float:
    title = normalize_text(item.title)
    if title in GENERIC_TITLES or len(content_tokens) <= 3 or len(item.content.strip()) < 24:
        return weight
    return 0.0


def score_memory_item(
    query: str,
    item: CareerMemoryItem,
    *,
    all_items: list[CareerMemoryItem] | None = None,
    weights: MemoryScoringWeights | None = None,
    now: datetime | None = None,
) -> MemoryScore:
    """Calculate a calibrated score with an inspectable explanation."""
    config = weights or MemoryScoringWeights()
    query_tokens = set(extract_keywords(query, limit=100))
    if not query_tokens:
        return MemoryScore(final_score=0.0)
    content_tokens = set(extract_keywords(f"{item.title} {item.content}", limit=300))
    tag_tokens = set(extract_keywords(" ".join(item.tags), limit=100))
    matched_content = sorted(query_tokens & content_tokens)
    matched_tags = sorted(query_tokens & tag_tokens)
    overlap = len(matched_content) / len(query_tokens)
    tag_overlap = len(matched_tags) / len(query_tokens)
    phrase = float(
        bool(normalize_text(query) and normalize_text(query) in normalize_text(item.content))
    )
    reference = now or datetime.now(UTC)
    updated = item.updated_at if item.updated_at.tzinfo else item.updated_at.replace(tzinfo=UTC)
    age_days = max(0, (reference - updated).days)
    recency = max(0.0, 1 - min(age_days, 730) / 730)
    generic_penalty = _generic_penalty(item, content_tokens, config.generic_penalty)
    stale_penalty = config.stale_penalty if age_days > 730 and overlap <= 0.5 else 0.0
    feedback, feedback_reason = evidence_feedback_adjustment(item, all_items or [])
    outcome, outcome_reason = outcome_adjustment(item)
    components = {
        "keyword_overlap": overlap * config.keyword_overlap,
        "tag_overlap": tag_overlap * config.tag_overlap,
        "kind_boost": config.kind_boosts.get(item.kind, 0.0),
        "phrase_boost": phrase * config.phrase_boost,
        "recency": recency * config.recency_boost,
        "feedback": feedback,
        "outcome": outcome,
        "generic_penalty": -generic_penalty,
        "stale_penalty": -stale_penalty,
    }
    raw_score = sum(components.values()) * item.confidence
    reasons = []
    if matched_content:
        reasons.append(f"contém termos da vaga: {', '.join(matched_content[:5])}")
    if matched_tags:
        reasons.append(f"tags compatíveis: {', '.join(matched_tags[:5])}")
    if feedback_reason:
        reasons.append(feedback_reason)
    if outcome_reason:
        reasons.append(outcome_reason)
    if generic_penalty:
        reasons.append("memória genérica recebeu penalidade")
    if stale_penalty:
        reasons.append("memória antiga com baixa aderência recebeu penalidade")
    return MemoryScore(
        final_score=round(max(0.0, min(1.0, raw_score)), 4),
        components={key: round(value, 4) for key, value in components.items() if value},
        reasons=reasons or ["tipo e recência tornaram esta memória relevante"],
    )
