"""Stores built with their default path live in SOTUHIRE_DATA_DIR, never in ./data.

Found by the Assertiva read-only guard (2026-11-15): rendering the Streamlit app in advanced mode
(tests/test_memory_ui.py) rewrote data/memory/career-profile.json in the developer's checkout,
because CareerProfileStore defaulted to a path relative to the working directory while the suite
pointed SOTUHIRE_DATA_DIR at an isolated folder. Four more stores had the same default.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from modules.opportunities.opportunity_store import OpportunityStore
from modules.portfolio.store import ProjectAnalysisStore
from modules.profile.career_profile import CareerProfileStore
from modules.scraping.cache import ScrapingCache
from modules.security.local_auth import LocalAuthManager


def _paths() -> dict[str, Path]:
    return {
        "career profile": CareerProfileStore().path,
        "opportunities": OpportunityStore().path,
        "project analyses": ProjectAnalysisStore().path,
        "scraping cache": ScrapingCache().directory,
        "installation token": LocalAuthManager()._store.path,
    }


@pytest.mark.parametrize("name", list(_paths()))
def test_default_store_paths_live_in_the_configured_data_dir(
    name: str, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    path = _paths()[name]
    assert path.is_relative_to(tmp_path), (name, path)


def test_the_memory_page_store_follows_the_data_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path.parent)  # a relative default would land in <cwd>/data
    store = CareerProfileStore()
    from modules.profile.schemas import CareerProfile

    store.save(CareerProfile())
    assert (tmp_path / "memory" / "career-profile.json").is_file()
    assert not (tmp_path.parent / "data").exists()
