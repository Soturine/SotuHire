"""Base connector contract for job sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from modules.core.schemas import JobPosting, JobSearchQuery, SourceStatus


class JobSourceConnector(ABC):
    """Base interface for public/manual job source connectors."""

    source_name: str = "unknown"
    status: SourceStatus = SourceStatus.PLANNED

    @abstractmethod
    def search(self, query: JobSearchQuery) -> list[JobPosting]:
        """Search jobs for a query."""

    def parse(self, raw: str) -> list[JobPosting]:
        """Parse raw content into normalized postings."""
        return []
