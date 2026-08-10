from __future__ import annotations

from modules.opportunities import (
    OpportunityCandidate,
    OpportunityPreferences,
    deduplicate_opportunities,
    rank_opportunities,
)


def _candidate(index: int, **updates: object) -> OpportunityCandidate:
    payload: dict[str, object] = {
        "source": "greenhouse",
        "source_kind": "greenhouse",
        "source_url": f"https://jobs.example.invalid/{index}",
        "external_id": str(index),
        "title": f"Engenheira de Dados {index}",
        "organization": "Empresa Ficticia",
        "location": "Remoto - Brasil",
        "description": "Python SQL dados senior",
        "employment_type": "Full-time",
        "remote": True,
    }
    payload.update(updates)
    return OpportunityCandidate.model_validate(payload)


def test_dedupe_uses_provider_id_url_and_full_identity_but_never_title_only() -> None:
    first = _candidate(1)
    same_url = _candidate(
        2,
        source="rss",
        source_kind="rss",
        source_url="https://jobs.example.invalid/1?utm_source=feed",
    )
    same_title_other_company = _candidate(
        3,
        title=first.title,
        organization="Outra Empresa Ficticia",
    )

    merged = deduplicate_opportunities([first, same_url, same_title_other_company])

    assert len(merged) == 2
    assert merged[0].duplicate_count == 1
    assert merged[0].merge_reasons == ["canonical_url"]
    assert len(merged[0].candidate.provenance) == 2
    assert merged[1].candidate.organization == "Outra Empresa Ficticia"


def test_local_ranking_calls_optional_ai_only_after_bounded_top_k() -> None:
    candidates = [_candidate(index) for index in range(30)]
    calls: list[str] = []
    preferences = OpportunityPreferences(
        target_titles=["Engenheira de Dados"],
        skills=["Python", "SQL"],
        locations=["Brasil"],
        remote_preferred=True,
        seniority=["senior"],
    )

    ranked = rank_opportunities(
        candidates,
        preferences,
        top_k=4,
        ai_enricher=lambda item: calls.append(item.external_id) or {"review": True},
    )

    assert len(ranked) == len(calls) == 4
    assert all(item.fit_score > 70 for item in ranked)
    assert all(item.confidence != item.evidence_coverage for item in ranked)
    assert all(item.ai_enrichment == {"review": True} for item in ranked)
