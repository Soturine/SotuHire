from modules.core.schemas import JobSearchQuery, Seniority
from modules.search_intelligence.post_detector import detect_opportunity_post
from modules.search_intelligence.query_generator import generate_all_queries


def test_generate_queries_contains_domain_search():
    query = JobSearchQuery(role="Analista de Dados", seniority=Seniority.JUNIOR, skills=["SQL"])
    queries = generate_all_queries(query)
    assert any("site:gupy.io" in item for item in queries)


def test_detect_opportunity_post():
    result = detect_opportunity_post("Estamos contratando QA júnior remoto, envie currículo")
    confidence = result["confidence"]

    assert result["is_opportunity"] is True
    assert isinstance(confidence, int)
    assert confidence >= 30
