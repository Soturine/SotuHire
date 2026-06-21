import pytest
from modules.matching.models import (
    OTHER_PROFESSIONAL_REGISTRATION_OPTION,
    ProfessionalRegistrationInput,
)
from modules.matching.requirement_matcher import (
    classify_professional_credential,
    detect_professional_credentials,
    evidence_from_text,
    match_requirement,
    normalize_requirement,
)


@pytest.mark.parametrize(
    ("code", "expected_category"),
    [
        ("CRM", "professional_license"),
        ("CRO", "professional_license"),
        ("CRF", "professional_license"),
        ("COREN", "professional_license"),
        ("CREFITO", "professional_license"),
        ("CRN", "professional_license"),
        ("CRMV", "professional_license"),
        ("CRP", "professional_license"),
        ("CREF", "professional_license"),
        ("CREA", "professional_license"),
        ("CAU", "professional_license"),
        ("CFT", "professional_license"),
        ("CRT", "professional_license"),
        ("CRTR", "professional_license"),
        ("CRQ", "professional_license"),
        ("OAB", "professional_license"),
        ("CRC", "professional_license"),
        ("CRA", "professional_license"),
        ("CORECON", "professional_license"),
        ("CRB", "professional_license"),
        ("CRESS", "professional_license"),
        ("CRECI", "professional_license"),
        ("CONRERP", "professional_license"),
        ("CRBio", "professional_license"),
        ("MTE", "professional_registration"),
        ("DRT", "professional_registration"),
    ],
)
def test_professional_credentials_are_detected_and_classified(
    code: str,
    expected_category: str,
) -> None:
    credential = classify_professional_credential(code)
    detected = detect_professional_credentials(f"Registro {code} ativo")

    assert credential is not None
    assert credential.category == expected_category
    assert [item.code for item in detected] == [credential.code]


def test_required_professional_license_missing_generates_knockout_gap() -> None:
    requirement = normalize_requirement("CREA obrigatorio", importance="required")
    match = match_requirement(requirement, [])

    assert requirement.category == "professional_license"
    assert requirement.criticality == "knockout"
    assert match.match_status == "missing"
    assert match.gap_severity == "knockout"
    assert "adicione" not in match.safe_action.casefold()
    assert "inclua" not in match.safe_action.casefold()


def test_preferred_professional_license_missing_is_not_knockout() -> None:
    requirement = normalize_requirement("COREN desejavel", importance="preferred")
    match = match_requirement(requirement, [])

    assert requirement.criticality == "medium"
    assert match.match_status == "missing"
    assert match.gap_severity == "medium"


def test_present_professional_license_increases_evidence_and_confidence() -> None:
    requirement = normalize_requirement("COREN obrigatorio", importance="required")
    evidence = evidence_from_text("COREN ativo numero 12345", source="resume")
    match = match_requirement(requirement, evidence)

    assert match.match_status == "matched"
    assert match.evidence_source == "resume"
    assert match.confidence >= 0.9
    assert match.candidate_evidence[0].category == "professional_license"


def test_mte_and_drt_are_professional_registrations() -> None:
    mte = normalize_requirement("MTE obrigatorio", importance="required")
    drt = normalize_requirement("DRT obrigatorio", importance="required")

    assert mte.category == "professional_registration"
    assert drt.category == "professional_registration"
    assert mte.criticality == "knockout"
    assert drt.criticality == "knockout"


@pytest.mark.parametrize(
    ("raw", "normalized_name", "category"),
    [
        ("BNCC", "BNCC", "regulation"),
        ("SIEM", "SIEM", "tool"),
        ("SOC", "SOC", "other"),
        ("AutoCAD", "AutoCAD", "software"),
        ("Revit", "Revit", "software"),
    ],
)
def test_domain_aliases_are_normalized(raw: str, normalized_name: str, category: str) -> None:
    requirement = normalize_requirement(raw)

    assert requirement.normalized_name == normalized_name
    assert requirement.category == category


def test_generic_professional_registration_option_is_accepted() -> None:
    registration = ProfessionalRegistrationInput(
        type="professional_registration",
        council=OTHER_PROFESSIONAL_REGISTRATION_OPTION,
        region="SP",
        number_present=True,
        status="unknown",
        confidence=0.85,
    )

    assert registration.council == OTHER_PROFESSIONAL_REGISTRATION_OPTION
    assert registration.number_present is True
