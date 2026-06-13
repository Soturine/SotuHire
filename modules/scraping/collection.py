"""High-level collection orchestration."""

from __future__ import annotations

from modules.opportunities.opportunity_store import OpportunityStore
from modules.scraping.connectors.configured_source import ConfiguredSourceConnector
from modules.scraping.schemas import CollectionResult, ScrapingSource
from modules.scraping.source_registry import default_source_registry


def collect_public_source(
    source: ScrapingSource,
    *,
    store: OpportunityStore | None = None,
    persist: bool = True,
) -> CollectionResult:
    """Collect one public source and persist deduplicated opportunities."""
    result = ConfiguredSourceConnector(default_source_registry()).collect(source)
    if result.opportunities and persist:
        summary = (store or OpportunityStore()).save_many(result.opportunities)
        result = result.model_copy(
            update={
                "new_count": summary.new_count,
                "duplicate_count": summary.duplicate_count,
                "updated_count": summary.updated_count,
            }
        )
    return result
