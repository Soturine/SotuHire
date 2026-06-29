from modules.ai.prompt_loader import default_prompt_registry


def test_default_prompt_registry_lists_initial_prompts() -> None:
    registry = default_prompt_registry()

    assert registry.list_prompt_ids() == [
        "ats_analysis_v1",
        "career_advice_v1",
        "domain_classification_v1",
        "github_repo_analysis_v2",
        "job_extraction_multi_domain_v1",
        "job_radar_match_explanation_v1",
        "job_wishlist_builder_v1",
        "match_analysis_evidence_based_v1",
        "resume_extraction_v1",
        "resume_tailor_v1",
        "source_import_enrichment_v1",
    ]


def test_prompt_registry_renders_user_template() -> None:
    registry = default_prompt_registry()

    rendered = registry.render_user_prompt(
        "domain_classification_v1",
        {
            "text": "Vaga de enfermagem com COREN.",
            "text_type": "job",
            "known_context": {},
            "language": "pt-BR",
        },
    )

    assert "Vaga de enfermagem com COREN" in rendered
    assert registry.output_schema("resume_extraction_v1").__name__ == "ResumeExtractionOutput"
