"""Domain vocabularies that several layers share must not drift.

Most of them now have one owner and are imported. The requirement importance and criticality
literals stay defined twice because the pure matching models cannot import modules.ai without
loading that package's eager __init__ (which imports the analyzer, which imports matching.models).
Those copies are pinned here instead.
"""

from __future__ import annotations

from typing import get_args

from apps.api.routes import career_intelligence
from apps.api.schemas.analysis import Recommendation as ApiRecommendation
from modules.ai.schemas import job_extraction
from modules.github_analyzer import schemas as github_schemas
from modules.local_api.compatibility import ENABLED_EXTENSION_FLOWS
from modules.matching import domain_weights
from modules.matching import models as matching_models
from modules.portfolio import schemas as portfolio_schemas
from modules.schemas.job_analysis import Recommendation


def test_requirement_vocabularies_match_between_ai_extraction_and_matching():
    assert get_args(matching_models.RequirementImportance) == get_args(
        job_extraction.RequirementImportance
    )
    assert get_args(matching_models.RequirementCriticality) == get_args(
        job_extraction.RequirementCriticality
    )


def test_recommendation_has_one_owner():
    assert matching_models.RecommendationAction is Recommendation
    assert ApiRecommendation is Recommendation
    from modules.ai.providers.gemini_provider import GeminiProvider  # noqa: F401  (schema below)
    from modules.analyzer import recommendation

    assert recommendation.Recommendation is Recommendation


def test_gemini_response_schema_lists_exactly_the_recommendations():
    import inspect

    from modules.ai.providers import gemini_provider

    source = inspect.getsource(gemini_provider)
    assert '"enum": list(get_args(Recommendation))' in source
    assert get_args(Recommendation) == (
        "apply",
        "apply_with_adjustments",
        "save_for_later",
        "ignore",
    )


def test_domain_list_and_grade_and_flows_have_one_owner():
    assert get_args(domain_weights.CareerDomain) == career_intelligence.DOMAINS
    assert github_schemas.Grade is portfolio_schemas.Grade
    assert ENABLED_EXTENSION_FLOWS == ("job", "public_exam", "github", "profile_evidence")


def test_job_extraction_vocabularies_are_owned_by_the_schema():
    import inspect

    from modules.ai import structured_job_extractor as extractor

    assert extractor.JobWorkModel is job_extraction.JobWorkModel
    assert extractor.JobContractType is job_extraction.JobContractType
    assert extractor.JobSeniorityLevel is job_extraction.JobSeniorityLevel
    source = inspect.getsource(extractor)
    assert "get_args(RequirementCategory)" in source
    assert "get_args(RequirementCriticality)" in source


def test_data_health_checks_every_store_the_legacy_migration_imports():
    import inspect

    from modules.storage import health
    from modules.storage.legacy_migration import LEGACY_PATHS

    assert health.LEGACY_PATHS is LEGACY_PATHS
    assert "for relative in LEGACY_PATHS" in inspect.getsource(health._check_legacy_files)
