"""High-level collection orchestration."""

from __future__ import annotations

from modules.opportunities.opportunity_store import OpportunityStore
from modules.scraping.connectors.configured_source import ConfiguredSourceConnector
from modules.scraping.connectors.manual_url import opportunity_from_text
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


def capture_user_assisted_opportunity(
    text: str,
    *,
    source_url: str = "",
    title_hint: str = "",
    source_name: str = "Captura assistida pelo usuário",
    store: OpportunityStore | None = None,
    persist: bool = True,
) -> CollectionResult:
    """Process only the current page content explicitly supplied by the user."""
    source = ScrapingSource(
        name=source_name,
        type="user_assisted_capture",
        url=source_url.strip() or "user-assisted://current-page",
        collection_mode="USER_ASSISTED_CAPTURE",
        enabled=True,
        max_items=1,
    )
    clean_text = text.strip()
    if not clean_text:
        return CollectionResult(
            source=source,
            failures=["Cole o conteúdo visível da vaga atual antes de capturar."],
            user_assisted_capture=True,
        )
    opportunity = opportunity_from_text(
        clean_text,
        source=source.name,
        source_url=source.url,
        title_hint=title_hint,
        confidence=0.95,
    )
    result = CollectionResult(
        source=source,
        opportunities=[opportunity],
        new_count=1,
        user_assisted_capture=True,
    )
    if persist:
        summary = (store or OpportunityStore()).save_many([opportunity])
        result = result.model_copy(
            update={
                "new_count": summary.new_count,
                "duplicate_count": summary.duplicate_count,
                "updated_count": summary.updated_count,
            }
        )
    return result
