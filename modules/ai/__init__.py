"""Structured AI helpers."""

from .domain_classification_service import (
    DomainClassificationServiceResult,
    classify_domain_structured,
)
from .providers import GeminiProvider, MockProvider, ProviderUnavailableError
from .structured_job_extractor import StructuredJobExtractionResult, extract_structured_job
from .structured_resume_extractor import (
    StructuredResumeExtractionResult,
    extract_structured_resume,
)
from .structured_analysis import StructuredAnalysisResult, analyze_structured, get_provider

__all__ = [
    "DomainClassificationServiceResult",
    "GeminiProvider",
    "MockProvider",
    "ProviderUnavailableError",
    "StructuredAnalysisResult",
    "StructuredJobExtractionResult",
    "StructuredResumeExtractionResult",
    "analyze_structured",
    "classify_domain_structured",
    "extract_structured_job",
    "extract_structured_resume",
    "get_provider",
]
