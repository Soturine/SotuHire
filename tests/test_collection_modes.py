from pathlib import Path

from modules.opportunities import OpportunityStore
from modules.scraping.collection import capture_user_assisted_opportunity
from modules.scraping.schemas import ScrapingSource


def test_collection_modes_are_explicit():
    public = ScrapingSource(name="Public", type="rss", url="https://example.com/jobs.xml")
    manual = ScrapingSource(
        name="Manual",
        type="manual_url",
        url="https://example.com/jobs/1",
        collection_mode="MANUAL_URL",
        max_items=1,
    )

    assert public.collection_mode == "PUBLIC_SCRAPING"
    assert manual.collection_mode == "MANUAL_URL"
    assert manual.max_items == 1


def test_user_assisted_capture_processes_only_supplied_current_page(tmp_path: Path):
    store = OpportunityStore(tmp_path / "opportunities.json")

    result = capture_user_assisted_opportunity(
        "Cargo: Dev Python\nEmpresa: Example\nPython SQL remoto",
        source_url="https://platform.example/current-job",
        store=store,
    )

    assert result.user_assisted_capture
    assert not result.scraping_performed
    assert result.source.collection_mode == "USER_ASSISTED_CAPTURE"
    assert result.opportunities[0].source_url == "https://platform.example/current-job"
    assert len(store.list()) == 1


def test_empty_user_assisted_capture_does_not_persist(tmp_path: Path):
    store = OpportunityStore(tmp_path / "opportunities.json")

    result = capture_user_assisted_opportunity("", store=store)

    assert result.failures
    assert not store.list()
