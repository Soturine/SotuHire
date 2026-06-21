"""Deterministic domain-intelligence helpers for multi-area analysis."""

from modules.domain_intelligence.domain_classifier import classify_domain
from modules.domain_intelligence.requirement_types import classify_requirement

__all__ = ["classify_domain", "classify_requirement"]
