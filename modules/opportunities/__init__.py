"""Collected opportunity normalization and local storage."""

from .intelligence import (
    OpportunityCandidate,
    OpportunityMerge,
    OpportunityPreferences,
    OpportunityProvenance,
    OpportunityRank,
    deduplicate_opportunities,
    rank_opportunities,
)
from .opportunity_filters import filter_opportunities
from .opportunity_normalizer import opportunity_to_job_posting
from .opportunity_store import OpportunityStore, StoreSummary

__all__ = [
    "OpportunityStore",
    "OpportunityCandidate",
    "OpportunityMerge",
    "OpportunityPreferences",
    "OpportunityProvenance",
    "OpportunityRank",
    "StoreSummary",
    "filter_opportunities",
    "deduplicate_opportunities",
    "rank_opportunities",
    "opportunity_to_job_posting",
]
