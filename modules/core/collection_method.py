"""Shared opportunity collection origin contract."""

from typing import Literal

CollectionMethod = Literal[
    "public_scraping",
    "manual_text",
    "manual_url",
    "csv_import",
    "json_import",
    "rss",
    "company_career_page",
    "browser_assisted_capture",
    "extension_capture",
    "companion_capture",
    "official_api_future",
    "demo_fixture",
]
