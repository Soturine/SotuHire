from __future__ import annotations

import json
from datetime import UTC, datetime

from modules.scraping.connectors.greenhouse import GreenhouseConnector
from modules.scraping.connectors.job_posting import parse_job_postings
from modules.scraping.connectors.lever import LeverConnector
from modules.scraping.connectors.rss_feed import RssFeedConnector, parse_feed_candidates
from modules.scraping.schemas import FetchResult, ScrapingSource


class FixtureClient:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.urls: list[str] = []

    def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult:
        del delay_seconds
        self.urls.append(url)
        return FetchResult(
            url=url,
            status_code=200,
            text=json.dumps(self.payload),
            collected_at=datetime(2026, 8, 1, tzinfo=UTC),
        )


def test_greenhouse_uses_public_listing_and_never_apply_endpoint() -> None:
    client = FixtureClient(
        {
            "meta": {"name": "Empresa Ficticia"},
            "jobs": [
                {
                    "id": 123,
                    "title": "Engenheira de Dados",
                    "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/123",
                    "location": {"name": "Remote - Brazil"},
                    "content": "<p>Python</p><script>secret()</script>",
                    "updated_at": "2026-08-01T12:00:00Z",
                    "metadata": [{"name": "Employment Type", "value": "Full-time"}],
                }
            ],
        }
    )
    source = ScrapingSource(
        name="Empresa Ficticia",
        type="greenhouse",
        url="https://job-boards.greenhouse.io/acme",
    )

    candidates = GreenhouseConnector(client).collect_candidates(source)

    assert client.urls == ["https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true"]
    assert candidates[0].external_id == "123"
    assert candidates[0].employment_type == "Full-time"
    assert "secret" not in candidates[0].description
    assert all("/apply" not in url for url in client.urls)


def test_lever_uses_public_postings_list_and_preserves_metadata() -> None:
    client = FixtureClient(
        [
            {
                "id": "lever-123",
                "text": "Analista Ficticia",
                "hostedUrl": "https://jobs.lever.co/acme/lever-123",
                "descriptionPlain": "SQL e qualidade.",
                "createdAt": 1785585600000,
                "workplaceType": "remote",
                "categories": {
                    "location": "Brasil",
                    "commitment": "Full-time",
                    "team": "Dados",
                },
            }
        ]
    )
    source = ScrapingSource(
        name="Empresa Ficticia",
        type="lever",
        url="https://jobs.lever.co/acme",
    )

    candidates = LeverConnector(client).collect_candidates(source)

    assert client.urls == ["https://api.lever.co/v0/postings/acme?mode=json"]
    assert candidates[0].source_kind == "lever"
    assert candidates[0].remote is True
    assert candidates[0].structured_data["team"] == "Dados"


def test_jobposting_supports_graph_arrays_nested_data_and_sanitizes_description() -> None:
    html = """
    <html><script type="application/ld+json">
    {"@context":"https://schema.org","@graph":[
      {"@type":"Organization","name":"Empresa Ficticia"},
      {"nested":{"@type":"JobPosting","identifier":{"value":"job-42"},
       "title":"Pessoa Engenheira","description":"<p>Python</p><img src=x onerror=bad()>",
       "datePosted":"2026-08-01","validThrough":"2026-09-01T23:59:00-03:00",
       "employmentType":["FULL_TIME"],
       "hiringOrganization":{"name":"Empresa Ficticia"},
       "jobLocation":{"address":{"addressLocality":"Recife","addressRegion":"PE","addressCountry":"BR"}},
       "baseSalary":{"currency":"BRL","value":{"minValue":100,"maxValue":200,"unitText":"DAY"}}}}
    ]}</script></html>
    """

    candidates = parse_job_postings(
        html,
        source_url="https://careers.example.invalid/jobs/42",
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.external_id == "job-42"
    assert candidate.organization == "Empresa Ficticia"
    assert candidate.location == "Recife, PE, BR"
    assert candidate.salary == {"currency": "BRL", "min": 100, "max": 200, "unit": "DAY"}
    assert candidate.description == "Python"


def test_rss_and_atom_preserve_guid_dates_and_conditional_validators() -> None:
    xml = """<?xml version="1.0"?><rss version="2.0"><channel>
      <item><guid>job-1</guid><title>Vaga Ficticia</title>
      <link>https://jobs.example.invalid/1</link><description>Python</description>
      <pubDate>Fri, 01 Aug 2026 12:00:00 GMT</pubDate></item>
    </channel></rss>"""
    candidates = parse_feed_candidates(
        xml,
        feed_url="https://jobs.example.invalid/feed.xml",
        source_name="Feed Ficticio",
    )
    assert candidates[0].external_id == "job-1"
    assert candidates[0].source_kind == "rss"
    assert candidates[0].posted_at is not None

    class ConditionalClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def fetch_conditional(
            self,
            url: str,
            *,
            etag: str = "",
            last_modified: str = "",
            delay_seconds: float = 2.0,
        ) -> FetchResult:
            del url, delay_seconds
            self.calls.append((etag, last_modified))
            if etag:
                return FetchResult(
                    url="https://jobs.example.invalid/feed.xml", status_code=304, not_modified=True
                )
            return FetchResult(
                url="https://jobs.example.invalid/feed.xml",
                status_code=200,
                text=xml,
                etag='"fixture-v1"',
                last_modified="Fri, 01 Aug 2026 12:00:00 GMT",
            )

        def fetch(self, url: str, *, delay_seconds: float = 2.0) -> FetchResult:
            raise AssertionError((url, delay_seconds))

    client = ConditionalClient()
    connector = RssFeedConnector(client)
    source = ScrapingSource(
        name="Feed Ficticio",
        type="rss",
        url="https://jobs.example.invalid/feed.xml",
    )
    first = connector.collect(source)
    second = connector.collect(source)
    assert first.new_count == 1
    assert second.new_count == 0
    assert client.calls[1][0] == '"fixture-v1"'
