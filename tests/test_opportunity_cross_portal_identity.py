from modules.core.opportunity_identity import same_opportunity


def test_same_opportunity_matches_similar_title_and_same_company_across_portals():
    assert same_opportunity(
        left_title="Pessoa Desenvolvedora Backend Junior",
        left_company="Example Tech",
        left_urls=["https://network.example/jobs/123"],
        right_title="Desenvolvedora Backend Júnior",
        right_company="Example Tech",
        right_url="https://careers.example/jobs/abc",
    )


def test_same_opportunity_does_not_merge_different_companies():
    assert not same_opportunity(
        left_title="Analista de Dados Junior",
        left_company="Example One",
        left_urls=["https://network.example/jobs/123"],
        right_title="Analista Dados Júnior",
        right_company="Example Two",
        right_url="https://careers.example/jobs/abc",
    )
