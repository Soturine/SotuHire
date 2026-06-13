"""Responsible public opportunity collection."""

from .client import ScrapingClient
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
    "ScrapingSource",
    "SourceRegistry",
    "SourceSafety",
    "inspect_source_safety",
    "default_source_registry",
]
