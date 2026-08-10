"""Adapters between the canonical intelligence contract and legacy collection DTOs."""

from __future__ import annotations

from modules.core.collection_method import CollectionMethod
from modules.opportunities.intelligence import OpportunityCandidate
from modules.scraping.schemas import ScrapedOpportunity


def candidate_to_scraped(candidate: OpportunityCandidate) -> ScrapedOpportunity:
    collection_method: CollectionMethod = (
        "official_api" if candidate.source_kind in {"greenhouse", "lever"} else "public_scraping"
    )
    return ScrapedOpportunity(
        source=candidate.source,
        source_url=candidate.source_url,
        title=candidate.title,
        company=candidate.organization or None,
        location=candidate.location or None,
        modality="remote" if candidate.remote else None,
        contract_type=candidate.employment_type or None,
        salary_text=str(candidate.salary.get("text", "")) or None,
        description=candidate.description,
        collected_at=candidate.collected_at,
        content_hash=candidate.content_hash,
        confidence=0.9 if candidate.source_kind in {"greenhouse", "lever"} else 0.75,
        collection_method=collection_method,
    )


__all__ = ["candidate_to_scraped"]
