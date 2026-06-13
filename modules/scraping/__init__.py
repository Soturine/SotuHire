"""Responsible public opportunity collection."""

from .cache import ScrapingCache
from .client import ScrapingClient
from .dedupe import deduplicate_opportunities, normalize_url
from .robots import inspect_source_safety
from .schemas import (
    CollectionMode,
    CollectionResult,
    FetchResult,
    ScrapedOpportunity,
    ScrapingSource,
    SourceSafety,
)
from .source_registry import SourceRegistry, default_source_registry

__all__ = [
    "CollectionResult",
    "CollectionMode",
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
