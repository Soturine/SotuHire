"""Deterministic A/B measurements for Career Context and local RAG policies."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ContextScenarioObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str
    claimed_evidence_refs: list[str] = Field(default_factory=list)
    confirmed_evidence_refs: list[str] = Field(default_factory=list)
    unconfirmed_evidence_refs: list[str] = Field(default_factory=list)
    usefulness: float = Field(ge=0, le=1)
    latency_ms: int = Field(ge=0)
    tokens: int = Field(ge=0)


def evaluate_context_scenario(observation: ContextScenarioObservation) -> dict[str, float | int]:
    """Measure evidence use without treating unconfirmed context as fact."""
    claimed = set(observation.claimed_evidence_refs)
    confirmed = set(observation.confirmed_evidence_refs)
    unconfirmed = set(observation.unconfirmed_evidence_refs)
    supported = claimed & confirmed
    unsupported = claimed - confirmed
    return {
        "evidence_precision": len(supported) / len(claimed) if claimed else 1.0,
        "unsupported_claim_rate": len(unsupported) / len(claimed) if claimed else 0.0,
        "unconfirmed_fact_rate": len(claimed & unconfirmed) / len(claimed) if claimed else 0.0,
        "confirmed_evidence_usage_rate": len(supported) / len(confirmed) if confirmed else 0.0,
        "usefulness": observation.usefulness,
        "latency_ms": observation.latency_ms,
        "tokens": observation.tokens,
    }


__all__ = ["ContextScenarioObservation", "evaluate_context_scenario"]
