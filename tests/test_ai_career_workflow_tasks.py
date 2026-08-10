from __future__ import annotations

from modules.ai.career_workflows import run_career_workflow_ai
from modules.ai.prompt_loader import default_prompt_registry
from modules.ai.task_registry import default_ai_task_registry
from modules.context import CareerContextPurpose

TASKS = {
    "interview_question_generation",
    "interview_answer_drafting",
    "star_story_structuring",
    "follow_up_drafting",
    "career_plan_explanation",
    "certification_recommendation_explanation",
    "project_gap_recommendation",
    "opportunity_enrichment",
    "taxonomy_mapping_explanation",
}


def test_new_tasks_have_versioned_prompts_schemas_fallback_and_context_purpose() -> None:
    prompts = default_prompt_registry()
    registry = default_ai_task_registry(prompts)

    for task_id in TASKS:
        task = registry.get(task_id)
        prompt = prompts.get(task.prompt_id, task.prompt_version)
        assert task.fallback_available
        assert task.structured_output_required
        assert prompt.output_schema is task.output_schema
        assert task.context_purpose in {purpose.value for purpose in CareerContextPurpose}
        rendered = prompt.render_user_prompt(
            {
                "language": "pt-BR",
                "context": "contexto minimo",
                "evidence": ["fixture://confirmed"],
                "request": "rascunho",
            }
        )
        assert "SOTUHIRE_UNTRUSTED_DATA" in rendered


def test_external_provider_requires_opt_in_and_errors_are_redacted(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SOTUHIRE_DATA_DIR", str(tmp_path))

    class Provider:
        name = "gemini"
        model = "fixture-model"

        def __init__(self) -> None:
            self.calls = 0

        def generate_structured(self, prompt, payload):  # noqa: ANN001, ANN201
            del prompt, payload
            self.calls += 1
            return {
                "questions": [
                    {
                        "category": "technical",
                        "question": "Como aplicou Python?",
                        "evidence_refs": ["fixture://python"],
                    }
                ],
                "evidence_refs": ["fixture://python"],
                "needs_user_review": True,
            }

    provider = Provider()
    local = run_career_workflow_ai(
        "interview_question_generation",
        {"evidence": ["fixture://python"]},
        provider=provider,
        external_ai_opt_in=False,
        source_refs=["fixture://python"],
    )
    external = run_career_workflow_ai(
        "interview_question_generation",
        {"evidence": ["fixture://python"]},
        provider=provider,
        external_ai_opt_in=True,
        source_refs=["fixture://python"],
    )

    assert provider.calls == 1
    assert local.provider_used == "local" and local.fallback_used
    assert external.provider_used == "gemini" and not external.fallback_used
    assert external.output["needs_user_review"] is True

    class BrokenProvider(Provider):
        def generate_structured(self, prompt, payload):  # noqa: ANN001, ANN201
            del prompt, payload
            raise RuntimeError("AQ.A1b2C3d4E5f6G7h8I9j0K1l2M3n4 secret")

    failed = run_career_workflow_ai(
        "taxonomy_mapping_explanation",
        {"request": "fixture"},
        provider=BrokenProvider(),
        external_ai_opt_in=True,
    )
    assert failed.provider_used == "local"
    assert "AQ.A1b2" not in str(failed.output)
