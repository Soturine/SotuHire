from __future__ import annotations

from modules.taxonomy import TaxonomyDatasetManifest, taxonomy_content_sha256
from modules.taxonomy.updater import TaxonomyUpdater


def _manifest(version: str, records: list[dict[str, str]]) -> TaxonomyDatasetManifest:
    return TaxonomyDatasetManifest(
        system="cbo",
        version=version,
        source_url="https://example.gov.br/taxonomy-fixture.json",
        license_name="Fixture oficial sem redistribuição",
        content_sha256=taxonomy_content_sha256(records),
    )


def test_taxonomy_update_requires_preview_apply_and_supports_rollback(tmp_path) -> None:
    updater = TaxonomyUpdater(tmp_path)
    first_records = [{"code": "1", "title": "Fixture 1"}]
    second_records = [{"code": "2", "title": "Fixture 2"}]

    first = updater.preview(_manifest("2026-01", first_records), first_records)
    assert updater.status("cbo").active_version == ""
    applied_first = updater.apply(first.preview_id)
    assert applied_first.active_version == "2026-01"

    second = updater.preview(_manifest("2026-02", second_records), second_records)
    applied_second = updater.apply(second.preview_id)
    assert applied_second.active_version == "2026-02"
    assert applied_second.previous_versions == ["2026-01"]

    rolled_back = updater.rollback("cbo")
    assert rolled_back.active_version == "2026-01"
    assert rolled_back.previous_versions[0] == "2026-02"
