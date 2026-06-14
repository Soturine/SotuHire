"""Shared opportunity collection origin contract."""

from typing import Literal

CollectionMethod = Literal[
    "public_scraping",
    "manual_url",
    "rss",
    "company_career_page",
    "browser_assisted_capture",
    "demo_fixture",
]
