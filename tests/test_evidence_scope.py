from __future__ import annotations

import pytest
from modules.context import (
    CareerContext,
    CareerContextEvidence,
    CareerContextPurpose,
    EvidenceReviewStatus,
    EvidenceScope,
    format_context_for_prompt,
)
from pydantic import ValidationError


def test_source_reference_is_provenance_not_confirmation() -> None:
    evidence = CareerContextEvidence(
        title="Python",
        content="Encontrado em documento importado.",
        source="resume.pdf",
        source_ref="fixture://resume/page/1",
    )

    assert evidence.review_status is EvidenceReviewStatus.SOURCED
    assert evidence.confirmed_by_user is False
    assert evidence.evidence_id.startswith("evidence-")
    assert len(evidence.content_hash) == 64


def test_immutable_scope_filters_external_ai_to_selected_confirmed_non_sensitive_evidence() -> None:
    confirmed = CareerContextEvidence(
        title="Confirmada",
        source_ref="fixture://confirmed",
        confirmed_by_user=True,
    )
    sourced = CareerContextEvidence(title="Com fonte", source_ref="fixture://sourced")
    sensitive = CareerContextEvidence(
        title="Sensível",
        source_ref="fixture://sensitive",
        confirmed_by_user=True,
        sensitive=True,
    )
    rejected = CareerContextEvidence(
        title="Rejeitada",
        review_status=EvidenceReviewStatus.REJECTED,
    )
    evidence = [confirmed, sourced, sensitive, rejected]
    scope = EvidenceScope.from_evidence(
        purpose=CareerContextPurpose.MATCH,
        evidence=evidence,
        selected_evidence_ids=[item.evidence_id for item in evidence],
        external_ai_opt_in=True,
    )

    assert scope.select(evidence) == [confirmed, sourced, sensitive]
    assert scope.select(evidence, for_external_ai=True) == [confirmed]
    with pytest.raises(ValidationError):
        scope.external_ai_opt_in = False  # type: ignore[misc]


def test_external_prompt_requires_scope_opt_in_and_excludes_sourced_only_item() -> None:
    confirmed = CareerContextEvidence(title="Confirmada", confirmed_by_user=True)
    sourced = CareerContextEvidence(title="Somente fonte", source_ref="fixture://source")
    evidence = [confirmed, sourced]
    without_opt_in = CareerContext(
        purpose=CareerContextPurpose.ATS,
        evidence=evidence,
        evidence_scope=EvidenceScope.from_evidence(
            purpose=CareerContextPurpose.ATS,
            evidence=evidence,
        ),
    )
    with_opt_in = without_opt_in.model_copy(
        update={
            "evidence_scope": EvidenceScope.from_evidence(
                purpose=CareerContextPurpose.ATS,
                evidence=evidence,
                external_ai_opt_in=True,
            )
        }
    )

    assert format_context_for_prompt(without_opt_in, external_ai=True) == ""
    external = format_context_for_prompt(with_opt_in, external_ai=True)
    assert "Confirmada" in external
    assert "Somente fonte" not in external
