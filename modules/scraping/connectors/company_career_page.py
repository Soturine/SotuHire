"""Collect likely vacancies from a public company career page."""

from __future__ import annotations

from modules.scraping.connectors.generic_public_page import GenericPublicPageConnector


class CompanyCareerPageConnector(GenericPublicPageConnector):
    """Specialized label for public company career pages."""
