"""Responsible public opportunity collection."""

from .cache import ScrapingCache
from .client import ScrapingClient
from .dedupe import deduplicate_opportunities, normalize_url
from .robots import inspect_source_safety
from .schemas import (
    CollectionResult,
    FetchResult,
    ScrapedOpportunity,
    ScrapingSource,
    SourceSafety,
)
from .source_registry import SourceRegistry, default_source_registry

__all__ = [
    "CollectionResult",
    "FetchResult",
    "ScrapedOpportunity",
    "ScrapingClient",
    "ScrapingCache",
    "ScrapingSource",
    "SourceRegistry",
    "SourceSafety",
    "inspect_source_safety",
    "default_source_registry",
    "deduplicate_opportunities",
    "normalize_url",
]
