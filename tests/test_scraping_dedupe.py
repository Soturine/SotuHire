from modules.scraping.connectors.manual_url import opportunity_from_text
from modules.scraping.dedupe import deduplicate_opportunities, normalize_url


def test_dedupe_normalizes_url_and_content():
    first = opportunity_from_text(
        "Cargo: Dev Python", source="a", source_url="https://example.com/job/1?utm_source=x"
    )
    second = opportunity_from_text(
        "Cargo: Dev Python", source="b", source_url="https://example.com/job/1"
    )

    unique, duplicates = deduplicate_opportunities([first, second])

    assert normalize_url(first.source_url) == second.source_url
    assert len(unique) == 1
    assert duplicates == 1
