"""The confirmation invariant has one owner, and both profile models obey it identically."""

from __future__ import annotations

import itertools

import pytest

from modules.evidence import EvidenceReviewStatus, reconcile_review_status
from modules.profile.context import ProfileContextItem
from modules.profile.models import ProfileItem

S = EvidenceReviewStatus
CASES = list(itertools.product(list(S), (False, True), ("", "doc-1#p2")))


def _oracle(status: S, confirmed: bool, source: str) -> tuple[S, bool]:
    """The rule as both validators wrote it before they shared one function."""
    if confirmed:
        status = S.CONFIRMED
    elif status == S.CONFIRMED:
        confirmed = True
    elif status == S.CANDIDATE and source:
        status = S.SOURCED
    if status in {S.REJECTED, S.STALE}:
        confirmed = False
    return status, confirmed


@pytest.mark.parametrize(("status", "confirmed", "source"), CASES)
def test_shared_rule_matches_the_previous_validators(status, confirmed, source):
    assert reconcile_review_status(
        status, confirmed_by_user=confirmed, has_source=bool(source)
    ) == _oracle(status, confirmed, source)


@pytest.mark.parametrize(("status", "confirmed", "source"), CASES)
def test_both_profile_models_reconcile_the_same_way(status, confirmed, source):
    common = {"review_status": status, "confirmed_by_user": confirmed, "source_ref": source}
    item = ProfileItem(type="skill", title="Atendimento", **common)
    context = ProfileContextItem(type="skill", title="Atendimento", **common)
    expected = _oracle(status, confirmed, source)
    assert (item.review_status, item.confirmed_by_user) == expected
    assert (context.review_status, context.confirmed_by_user) == expected


@pytest.mark.parametrize(("status", "confirmed", "source"), CASES)
def test_only_the_user_confirms(status, confirmed, source):
    result, by_user = reconcile_review_status(
        status, confirmed_by_user=confirmed, has_source=bool(source)
    )
    assert (result == S.CONFIRMED) == by_user
    if source and not confirmed and status != S.CONFIRMED:
        assert result != S.CONFIRMED  # a source never confirms on its own
