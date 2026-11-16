"""CP-UX03: the data search finds what the person typed regardless of accents and case.

Before: evidence used SQLite ``LIKE`` and portfolio ``casefold``, so "curriculo" missed
"Currículo", "pesquisa aplicada" missed "Pesquisa Aplicada" only when accented; Profile facts and
tracked applications were not searched at all. Sensitive Profile items must stay out.
"""

from __future__ import annotations

from modules.copilot_v2.search import SearchHit, fold, rank, score
from modules.profile.models import ProfileItem
from modules.profile.service import UniversalCareerProfileService
from modules.tracker.job_tracker import JobTracker
from tests.api_test_helpers import api_client


def test_fold_drops_accents_and_case() -> None:
    assert fold("Currículo de Saúde ÇÃO") == "curriculo de saude cao"


def test_every_word_must_appear_and_the_title_ranks_first() -> None:
    assert score("analise dados", "Análise de dados") == 100
    assert score("dados analise", "Análise de dados") == 60
    assert score("dados", "Projeto", "análise de dados") == 20
    assert score("dados financas", "Análise de dados") == 0


def test_rank_orders_by_score_and_keeps_ties_stable() -> None:
    hits = rank(
        "python",
        [
            (SearchHit("evidence", "a", "Projeto", "", "/evidence"), ("usa Python",)),
            (SearchHit("evidence", "b", "Python avançado", "", "/evidence"), ()),
            (SearchHit("evidence", "c", "Sem relação", "", "/evidence"), ()),
        ],
        limit=10,
    )
    assert [hit.entity_id for hit in hits] == ["b", "a"]


def test_api_searches_profile_and_applications_without_accents(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))
    client = api_client()
    client.post("/api/v2/evidence", json={"node_type": "research", "title": "Pesquisa Clínica"})
    profile = UniversalCareerProfileService()
    profile.add_item(ProfileItem(type="certification", title="Certificação em Gestão Clínica"))
    profile.add_item(ProfileItem(type="health", title="Condição clínica informada", sensitive=True))
    JobTracker().add_existing_application(job_title="Enfermeira Clínica", company="Hospital")

    found = client.get("/api/v2/search", params={"query": "clinica"}).json()["data"]

    by_type = {(row["entity_type"], row["title"]) for row in found}
    assert ("evidence", "Pesquisa Clínica") in by_type
    assert ("profile", "Certificação em Gestão Clínica") in by_type
    assert ("application", "Enfermeira Clínica") in by_type
    assert all(row["title"] != "Condição clínica informada" for row in found)
    routes = {row["entity_type"]: row["route"] for row in found}
    assert routes == {"evidence": "/evidence", "profile": "/profile", "application": "/tracker"}
