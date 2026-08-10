from __future__ import annotations

from pathlib import Path

import pytest
from modules.taxonomy import (
    MappingMethod,
    NormalizedOccupation,
    NormalizedSkill,
    TaxonomyDatasetManifest,
    TaxonomyNormalizer,
    VersionedTaxonomyStore,
    taxonomy_content_sha256,
)


def test_versioned_taxonomy_cache_verifies_manifest_and_is_content_addressed(
    tmp_path: Path,
) -> None:
    records = [{"code": "0000-00", "title": "Ocupacao Ficticia"}]
    manifest = TaxonomyDatasetManifest(
        system="cbo",
        version="fixture-1",
        source_url="https://www.gov.br/trabalho-e-emprego/fixture",
        license_name="Fonte oficial; fixture sem redistribuicao de dataset real",
        content_sha256=taxonomy_content_sha256(records),
    )
    store = VersionedTaxonomyStore(tmp_path)

    target = store.save(manifest, records)

    assert target.name == f"{manifest.content_sha256}.json"
    assert store.load(manifest) == records
    invalid = manifest.model_copy(update={"content_sha256": "0" * 64})
    with pytest.raises(ValueError, match="hash"):
        store.save(invalid, records)


def test_taxonomy_mapping_keeps_fuzzy_matches_reviewable_and_never_confirms_skill() -> None:
    occupation = NormalizedOccupation(
        occupation_id="occupation-data",
        canonical_title="Engenheira de Dados",
        aliases=["Data Engineer"],
        taxonomy_refs=["cbo:fixture", "esco:fixture"],
    )
    skill = NormalizedSkill(
        skill_id="skill-python",
        canonical_label="Python",
        aliases=["Python 3"],
        taxonomy_refs=["esco:fixture", "onet:fixture"],
    )
    normalizer = TaxonomyNormalizer(occupations=[occupation], skills=[skill])

    alias = normalizer.map_occupation("Data Engineer")
    fuzzy = normalizer.map_skill("Pythom")

    assert alias is not None and alias.match_method == MappingMethod.ALIAS
    assert alias.review_status == "candidate"
    assert fuzzy is not None and fuzzy.match_method == MappingMethod.SEMANTIC_CANDIDATE
    assert fuzzy.review_status == "candidate"
    assert "regulated" not in occupation.model_dump()
