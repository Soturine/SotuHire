from modules.resume_tailor.tailor_rules import (
    detect_tailor_warnings,
    should_emphasize_industrial_background,
)
from modules.schemas.resume_tailor import ResumeTailorOutput, TailoredResumeSection


def test_detects_industrial_context_for_embraer_like_jobs():
    assert should_emphasize_industrial_background("Vaga de dados para setor aeroespacial em SJC")


def test_tailor_output_warns_on_invented_information():
    output = ResumeTailorOutput(
        target_role="Estágio em Dados",
        tailored_sections=[
            TailoredResumeSection(
                section_name="Experiência",
                original_text="Projeto acadêmico em Python",
                tailored_text="Experiência profissional em Python por 3 anos",
                reason_for_change="Tentativa inválida de melhorar aderência",
                evidence_source="",
                invented_information=True,
            )
        ],
    )
    warnings = detect_tailor_warnings(output)
    assert len(warnings) >= 2
    assert not output.is_safe_to_export()
