"""Task-capability routing matrix shared by audits and provider selection."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from modules.ai.task_registry import default_ai_task_registry

ProviderCapabilityState = Literal[
    "supported",
    "degraded",
    "unsupported",
    "unverified",
    "blocked_external",
]


class AiTaskProviderRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    prompt_id: str
    output_schema: str
    context_purpose: str
    evidence_scope: str
    consumer: str
    providers: dict[str, ProviderCapabilityState] = Field(default_factory=dict)


_CONSUMERS = {
    "resume_extraction": "Resume ingestion",
    "job_extraction": "Job ingestion",
    "domain_classification": "Domain intelligence",
    "profile_item_extraction": "Profile",
    "lattes_extraction": "Academic profile",
    "public_exam_extraction": "Public exams",
    "match_explanation": "Match",
    "ats_review": "ATS",
    "resume_tailor": "Resume Tailor",
    "wishlist_builder": "Radar",
    "radar_explanation": "Radar",
    "source_enrichment": "Sources",
    "github_repo_analysis": "GitHub",
    "github_profile_analysis": "GitHub",
    "portfolio_gap_analysis": "Career plan",
    "career_advice": "Career guidance",
    "interview_question_generation": "Interviews",
    "interview_answer_drafting": "Interviews",
    "star_story_structuring": "STAR bank",
    "follow_up_drafting": "Follow-up drafts",
    "career_plan_explanation": "Career plan",
    "certification_recommendation_explanation": "Career actions",
    "project_gap_recommendation": "Career actions",
    "opportunity_enrichment": "Opportunity intelligence",
    "taxonomy_mapping_explanation": "Taxonomy review",
}


def provider_task_matrix(
    observed: dict[str, ProviderCapabilityState] | None = None,
) -> list[AiTaskProviderRoute]:
    """Return explicit support state; local servers stay unverified until user health-checks them."""
    observed = observed or {}
    routes = []
    for task in default_ai_task_registry().list():
        providers: dict[str, ProviderCapabilityState] = {
            "local_deterministic": "supported" if task.fallback_available else "unsupported",
            "gemini": observed.get("gemini", "supported"),
            "openai": observed.get("openai", "supported"),
            "ollama": observed.get("ollama", "unverified"),
            "lm_studio": observed.get("lm_studio", "unverified"),
            "openai_compatible": observed.get("openai_compatible", "unverified"),
        }
        routes.append(
            AiTaskProviderRoute(
                task_id=task.task_id,
                prompt_id=f"{task.prompt_id}@{task.prompt_version}",
                output_schema=task.output_schema.__name__,
                context_purpose=task.context_purpose,
                evidence_scope=task.sensitive_context_policy,
                consumer=_CONSUMERS.get(task.task_id, "registry consumer not documented"),
                providers=providers,
            )
        )
    return routes


__all__ = ["AiTaskProviderRoute", "ProviderCapabilityState", "provider_task_matrix"]
