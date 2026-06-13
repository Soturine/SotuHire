"""Collected opportunity normalization and local storage."""

from .opportunity_filters import filter_opportunities
from .opportunity_normalizer import opportunity_to_job_posting
from .opportunity_store import OpportunityStore, StoreSummary

__all__ = [
    "OpportunityStore",
    "StoreSummary",
    "filter_opportunities",
    "opportunity_to_job_posting",
]
