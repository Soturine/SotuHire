"""Credential claims a suggestion asserts, and which of them the evidence does not hold (SH-NEW-014)."""

from __future__ import annotations

import pytest
from modules.ai.claim_validation import credential_claims, unsupported_credential_claims


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Registro ativo no CRM e Doutorado em Saúde Coletiva.", ["CRM", "doutorado"]),
        ("PhD in Chemical Engineering", ["doutorado"]),
        ("Pós-doutorado em biologia", ["pós-doutorado"]),
        ("Mestrado em Educação; MBA executivo", ["mestrado", "MBA"]),
        ("Pós-graduação lato sensu em gestão", ["especialização/pós-graduação"]),
        ("Advogada inscrita na OAB/SP", ["OAB"]),
        ("Enfermeira com COREN ativo", ["COREN"]),
    ],
)
def test_registrations_and_graduate_degrees_are_recognized(text, expected):
    assert credential_claims(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Mestre de obras com 10 anos de canteiro",  # an occupation, not a degree
        "Doutorando em física",  # in progress, not held
        "Sistemas embarcados e funções Lambda",  # 'mba' inside words
        "Aplicação de protocolos de qualidade",
        "",
    ],
)
def test_words_that_only_look_like_credentials_are_not_claims(text):
    assert credential_claims(text) == []


def test_only_claims_missing_from_every_evidence_text_are_unsupported():
    text = "CRM ativo, doutorado e MBA."
    evidence = ["Médica com registro no CRM-SP.", "Doutorado concluído em 2019."]
    assert unsupported_credential_claims(text, evidence) == ["MBA"]
    assert unsupported_credential_claims(text, []) == ["CRM", "doutorado", "MBA"]
    assert unsupported_credential_claims("Atendimento ao cliente", []) == []
