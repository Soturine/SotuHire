import pytest
from modules.resume_tailor.tailor_rules import should_emphasize_industrial_background
from modules.schemas.resume_tailor import TailoredResumeSection
from pydantic import ValidationError


def test_detects_industrial_context_for_embraer_like_jobs():
    assert should_emphasize_industrial_background("Vaga de dados para setor aeroespacial em SJC")


def test_tailor_output_rejects_invented_information():
    with pytest.raises(ValidationError):
        TailoredResumeSection(
            section_name="Experiência",
            original_text="Projeto acadêmico em Python",
            tailored_text="Experiência profissional em Python por 3 anos",
            reason_for_change="Tentativa inválida de melhorar aderência",
            evidence_source="currículo mestre",
            invented_information=True,
        )
