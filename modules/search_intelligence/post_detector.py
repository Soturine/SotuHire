"""Detect informal job opportunities in social posts."""

from __future__ import annotations

STRONG_SIGNALS = [
    "estamos contratando",
    "vaga aberta",
    "contratando",
    "envie currículo",
    "envie curriculo",
    "oportunidade",
    "me chama no inbox",
    "link da vaga",
]

MEDIUM_SIGNALS = [
    "time crescendo",
    "novas posições",
    "novas posicoes",
    "indicação",
    "indicacao",
    "conhece alguém",
    "conhece alguem",
]


def detect_opportunity_post(text: str) -> dict[str, object]:
    """Classify a text as a possible hidden job post."""
    normalized = text.lower()
    strong = [signal for signal in STRONG_SIGNALS if signal in normalized]
    medium = [signal for signal in MEDIUM_SIGNALS if signal in normalized]
    score = min(100, len(strong) * 30 + len(medium) * 15)
    return {
        "is_opportunity": score >= 30,
        "confidence": score,
        "strong_signals": strong,
        "medium_signals": medium,
    }
