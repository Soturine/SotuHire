"""Common registry of production AI tasks and their evaluation contracts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pydantic import BaseModel

from modules.ai.prompt_registry import PromptRegistry


class AiTaskRegistryError(LookupError):
    """Raised when a task or prompt binding is invalid."""


@dataclass(frozen=True, slots=True)
class AiTask:
    """One measurable AI task bound to a versioned production prompt."""

    task_id: str
    prompt_id: str
    prompt_version: str
    input_schema: str
    output_schema: type[BaseModel]
    providers_supported: tuple[str, ...]
    structured_output_required: bool
    fallback_available: bool
    context_purpose: str
    sensitive_context_policy: str
    evaluation_suite: str
    default_metrics: tuple[str, ...]


class AiTaskRegistry:
    """Resolve tasks and ensure that every production prompt has one owner."""

    def __init__(self, tasks: Iterable[AiTask], prompts: PromptRegistry) -> None:
        self._tasks: dict[str, AiTask] = {}
        self._by_prompt: dict[str, AiTask] = {}
        for task in tasks:
            if task.task_id in self._tasks:
                raise AiTaskRegistryError(f"Duplicate AI task: {task.task_id}")
            if task.prompt_id in self._by_prompt:
                raise AiTaskRegistryError(f"Prompt has multiple task owners: {task.prompt_id}")
            spec = prompts.get(task.prompt_id, task.prompt_version)
            if spec.output_schema is not task.output_schema:
                raise AiTaskRegistryError(f"Output schema mismatch for task: {task.task_id}")
            self._tasks[task.task_id] = task
            self._by_prompt[task.prompt_id] = task
        orphan_prompts = set(prompts.list_prompt_ids()) - set(self._by_prompt)
        if orphan_prompts:
            raise AiTaskRegistryError(
                "Production prompts without task: " + ", ".join(sorted(orphan_prompts))
            )

    def get(self, task_id: str) -> AiTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise AiTaskRegistryError(f"AI task not registered: {task_id}") from exc

    def for_prompt(self, prompt_id: str) -> AiTask:
        try:
            return self._by_prompt[prompt_id]
        except KeyError as exc:
            raise AiTaskRegistryError(f"Production prompt has no AI task: {prompt_id}") from exc

    def list(self) -> list[AiTask]:
        return [self._tasks[key] for key in sorted(self._tasks)]


_DEFAULT_METRICS = (
    "schema_validity",
    "required_field_completion",
    "evidence_precision",
    "unsupported_claim_rate",
    "confidence_calibration_error",
    "latency_p50",
    "estimated_cost",
)


def default_ai_task_registry(prompts: PromptRegistry | None = None) -> AiTaskRegistry:
    """Build the complete v1.9.7 task registry."""
    if prompts is None:
        from modules.ai.prompt_loader import default_prompt_registry

        prompts = default_prompt_registry()
    definitions = (
        (
            "resume_extraction",
            "resume_extraction_v1",
            "ResumeExtractionInput@1",
            "resume",
            "confirmed_profile_only",
        ),
        (
            "job_extraction",
            "job_extraction_multi_domain_v1",
            "JobExtractionInput@1",
            "job",
            "no_personal_context_required",
        ),
        (
            "domain_classification",
            "domain_classification_v1",
            "DomainClassificationInput@1",
            "classification",
            "minimum_necessary",
        ),
        (
            "profile_item_extraction",
            "profile_items_extractor_v1",
            "ProfileItemExtractionInput@1",
            "profile",
            "draft_only_no_auto_merge",
        ),
        (
            "lattes_extraction",
            "profile_lattes_extractor_v1",
            "LattesExtractionInput@1",
            "lattes",
            "draft_only_no_auto_merge",
        ),
        (
            "public_exam_extraction",
            "public_exam_notice_extractor_v1",
            "PublicExamExtractionInput@1",
            "public_exam",
            "eligibility_requires_confirmed_profile",
        ),
        (
            "match_explanation",
            "match_analysis_evidence_based_v1",
            "MatchAnalysisInput@1",
            "match",
            "external_context_opt_in_confirmed_only",
        ),
        (
            "ats_review",
            "ats_analysis_v1",
            "AtsReviewInput@1",
            "ats",
            "external_context_opt_in_confirmed_only",
        ),
        (
            "resume_tailor",
            "resume_tailor_v1",
            "ResumeTailorInput@1",
            "tailor",
            "external_context_opt_in_confirmed_only",
        ),
        (
            "wishlist_builder",
            "job_wishlist_builder_v1",
            "WishlistBuilderInput@1",
            "radar",
            "minimum_necessary_confirmed_only",
        ),
        (
            "radar_explanation",
            "job_radar_match_explanation_v1",
            "RadarExplanationInput@1",
            "radar",
            "no_sensitive_context",
        ),
        (
            "source_enrichment",
            "source_import_enrichment_v1",
            "SourceEnrichmentInput@1",
            "source",
            "no_personal_context_required",
        ),
        (
            "github_repo_analysis",
            "github_repo_analysis_v2",
            "GitHubRepoAnalysisInput@2",
            "github",
            "external_context_opt_in_confirmed_only",
        ),
        (
            "github_profile_analysis",
            "github_profile_analysis_v1",
            "GitHubProfileAnalysisInput@1",
            "github",
            "public_evidence_only",
        ),
        (
            "portfolio_gap_analysis",
            "portfolio_gap_analysis_v1",
            "PortfolioGapAnalysisInput@1",
            "portfolio",
            "confirmed_profile_and_public_evidence",
        ),
        (
            "career_advice",
            "career_advice_v1",
            "CareerAdviceInput@1",
            "career_advice",
            "external_context_opt_in_confirmed_only",
        ),
    )
    tasks: list[AiTask] = []
    for task_id, prompt_id, input_schema, purpose, policy in definitions:
        spec = prompts.get(prompt_id)
        tasks.append(
            AiTask(
                task_id=task_id,
                prompt_id=prompt_id,
                prompt_version=spec.version,
                input_schema=input_schema,
                output_schema=spec.output_schema,
                providers_supported=("local", "gemini", "openai"),
                structured_output_required=True,
                fallback_available=True,
                context_purpose=purpose,
                sensitive_context_policy=policy,
                evaluation_suite=spec.evaluation_suite,
                default_metrics=_DEFAULT_METRICS,
            )
        )
    return AiTaskRegistry(tasks, prompts)


__all__ = [
    "AiTask",
    "AiTaskRegistry",
    "AiTaskRegistryError",
    "default_ai_task_registry",
]
