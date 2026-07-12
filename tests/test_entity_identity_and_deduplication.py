from modules.core.deduplication import duplicate_groups, unique_preserving_order
from modules.core.entity_identity import (
    normalize_doi,
    normalize_entity_url,
    normalize_github_repo,
    normalize_orcid,
    profile_item_identity,
    public_exam_identity,
)
from modules.memory import CareerMemoryItem, MemoryStore
from modules.public_exams.models import ExamNotice
from modules.public_exams.store import PublicExamStore


def test_urls_remove_tracking_but_keep_meaningful_entity_ids() -> None:
    first = normalize_entity_url(
        "https://Jobs.Example/vaga?jobId=42&utm_source=mail&tracking=abc#details"
    )
    second = normalize_entity_url("https://jobs.example/vaga?jobId=42")
    other = normalize_entity_url("https://jobs.example/vaga?jobId=43")

    assert first == second
    assert first != other


def test_academic_and_repository_references_are_canonical() -> None:
    assert normalize_doi("https://doi.org/10.1234/ABC.Def.") == "10.1234/abc.def"
    assert normalize_orcid("https://orcid.org/0000-0002-1825-0097") == "0000-0002-1825-0097"
    assert normalize_github_repo("https://github.com/Example/Portfolio.git/tree/main") == (
        "example/portfolio"
    )


def test_profile_identity_deduplicates_same_source_ref_across_import_paths() -> None:
    manual = profile_item_identity(
        item_type="journal_article",
        title="Artigo com titulo abreviado",
        source="manual",
        source_ref="https://doi.org/10.1234/ABC.Def",
    )
    lattes = profile_item_identity(
        item_type="journal_article",
        title="Titulo completo do artigo",
        source="curriculum_lattes",
        source_ref="doi: 10.1234/abc.def",
    )

    assert manual == lattes


def test_profile_identity_keeps_provenance_out_of_semantic_fallback() -> None:
    manual = profile_item_identity(
        item_type="certification",
        title="NR10",
        source="manual",
        evidence="Certificado informado pela pessoa usuaria.",
    )
    imported = profile_item_identity(
        item_type="certification",
        title="NR10",
        source="certificate",
        evidence="Mesmo certificado vindo de outra fonte.",
    )

    assert manual == imported


def test_generic_deduplication_keeps_records_for_review() -> None:
    records = [
        {"id": "first", "key": "same"},
        {"id": "second", "key": "same"},
        {"id": "third", "key": "other"},
    ]

    groups = duplicate_groups(records, lambda item: item["key"])
    unique = unique_preserving_order(records, lambda item: item["key"])

    assert [[item["id"] for item in group] for group in groups] == [["first", "second"]]
    assert [item["id"] for item in unique] == ["first", "third"]
    assert len(records) == 3


def test_memory_store_deduplicates_same_source_reference_and_preserves_origins(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.jsonl")
    first = store.add_memory_item(
        CareerMemoryItem(
            kind="project_evidence",
            title="Repositorio Example/Portfolio",
            content="README evidencia pesquisa e Python.",
            source="github",
            source_id="https://github.com/example/portfolio?utm_source=profile",
        )
    )
    second = store.add_memory_item(
        CareerMemoryItem(
            kind="project_evidence",
            title="Portfolio publico",
            content="README atualizado evidencia pesquisa e Python.",
            source="extension_capture",
            source_id="https://github.com/example/portfolio",
        )
    )

    items = store.list_memory_items()
    assert len(items) == 1
    assert second.id == first.id
    assert items[0].source_refs == [
        "https://github.com/example/portfolio?utm_source=profile",
        "https://github.com/example/portfolio",
    ]
    assert items[0].deduplication_reason


def test_public_exam_store_consolidates_tracking_urls_without_deleting_history(tmp_path) -> None:
    store = PublicExamStore(tmp_path / "notices.json")
    first = store.save_notice(
        ExamNotice(
            title="Edital 01/2026",
            organization="Orgao Exemplo",
            source_url="https://example.org/edital/1?utm_source=mail",
            raw_text="Cargo Analista. Inscricoes em agosto.",
        )
    )
    second = store.save_notice(
        ExamNotice(
            title="Edital numero 01/2026 atualizado",
            organization="Orgao Exemplo",
            source_url="https://example.org/edital/1?tracking=portal",
            raw_text="Cargo Analista. Inscricoes prorrogadas.",
        )
    )

    notices = store.list_notices()
    assert len(notices) == 1
    assert second.notice_id == first.notice_id
    assert second.merged_notice_ids
    assert len(second.source_refs) == 2
    assert "consolidado" in second.warnings[-1].lower()


def test_public_exam_identity_uses_number_and_organization_without_url() -> None:
    first = public_exam_identity(
        notice_number="01/2026", organization="Orgao Exemplo", exam_board="Banca A"
    )
    second = public_exam_identity(
        notice_number="01/2026", organization="Orgao Exemplo", exam_board="Banca A"
    )

    assert first == second
