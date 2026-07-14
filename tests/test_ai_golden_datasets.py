from modules.ai.evaluation.dataset import iter_golden_cases
from modules.ai.task_registry import default_ai_task_registry

EXPECTED_DIRECTORIES = {
    "resume",
    "jobs",
    "match",
    "ats",
    "tailor",
    "lattes",
    "public_exams",
    "github",
    "wishlist",
    "source_enrichment",
    "career_advice",
}

EXPECTED_DOMAINS = {
    "engineering_technology",
    "nursing_health",
    "education_pedagogy",
    "research_lattes",
    "administration_commercial",
    "law",
    "chemistry_laboratory",
    "tourism_services",
    "arts_design",
    "public_exam",
    "career_transition",
    "no_formal_experience",
}

EXPECTED_ADVERSARIAL_TAGS = {
    "incomplete_resume",
    "short_ambiguous_job",
    "seniority_mismatch",
    "informal_experience",
    "free_course_like_degree",
    "missing_professional_registration",
    "publication_without_doi",
    "inconsistent_notice_dates",
    "duplicate_tracking",
    "prompt_injection",
    "document_ignore_rules",
    "malicious_content",
    "broken_characters",
    "invalid_json",
    "empty_response",
    "timeout",
    "rate_limit",
}


def test_golden_cases_cover_domains_contracts_and_adversarial_inputs() -> None:
    cases = iter_golden_cases()
    task_ids = {task.task_id for task in default_ai_task_registry().list()}
    tags = {tag for case in cases for tag in case.tags}

    assert {case.domain for case in cases} == EXPECTED_DOMAINS
    assert {case.task_id for case in cases} <= task_ids
    assert tags >= EXPECTED_ADVERSARIAL_TAGS
    assert all(case.forbidden_claims for case in cases)
    assert all(case.required_evidence_refs for case in cases)
    assert all(case.expected_confidence_range for case in cases)


def test_expected_golden_directories_exist() -> None:
    from pathlib import Path

    assert {
        path.name for path in Path("tests/golden").iterdir() if path.is_dir()
    } == EXPECTED_DIRECTORIES
