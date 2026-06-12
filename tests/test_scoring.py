from modules.core.scoring import clamp_score, weighted_score


def test_clamp_score():
    assert clamp_score(-10) == 0
    assert clamp_score(50.4) == 50
    assert clamp_score(200) == 100
    assert clamp_score(None) is None


def test_weighted_score_ignores_none():
    assert weighted_score({"a": 100, "b": None}, {"a": 1, "b": 1}) == 100
