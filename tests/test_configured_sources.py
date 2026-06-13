from pathlib import Path

from modules.scraping.connectors.configured_source import load_configured_sources


def test_configured_sources_are_loaded_from_toml(tmp_path: Path):
    target = tmp_path / "sources.toml"
    target.write_text(
        '[[sources]]\nname="Feed"\ntype="rss"\nurl="https://example.com/jobs.xml"\nenabled=true\n',
        encoding="utf-8",
    )

    sources = load_configured_sources(target)

    assert sources[0].enabled
    assert sources[0].type == "rss"
