from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from modules.security.credentials import (
    contains_provider_secret,
    looks_like_modern_gemini_key,
    redact_provider_secrets,
)
from scripts.scan_secrets import candidate_files, has_secret_pattern


def _synthetic_modern_gemini_key() -> str:
    return "AQ." + "Ab3dEf6hJk9mNp2Qr5St8VwXyZ0_"


def test_modern_gemini_detection_uses_shape_entropy_and_context(tmp_path: Path) -> None:
    secret = _synthetic_modern_gemini_key()
    credential_file = tmp_path / "settings.json"
    credential_file.write_text(f'{{"gemini_api_key":"{secret}"}}', encoding="utf-8")
    prose_file = tmp_path / "notes.txt"
    prose_file.write_text("A sigla AQ. aparece em um relatório normal.", encoding="utf-8")

    assert looks_like_modern_gemini_key(secret)
    assert contains_provider_secret(f"Gemini API key: {secret}")
    assert has_secret_pattern(credential_file)
    assert not has_secret_pattern(prose_file)


def test_modern_gemini_is_redacted_from_json_and_logs() -> None:
    secret = _synthetic_modern_gemini_key()
    sanitized = redact_provider_secrets(f'{{"error":"API key {secret} inválida"}}')

    assert secret not in sanitized
    assert "[REDACTED]" in sanitized
    assert redact_provider_secrets("AQ. é uma sigla") == "AQ. é uma sigla"


def test_secret_scanner_checks_zip_members_without_exposing_value(tmp_path: Path) -> None:
    secret = _synthetic_modern_gemini_key()
    bundle = tmp_path / "bundle.zip"
    with ZipFile(bundle, "w") as archive:
        archive.writestr("runtime.js", f"// gemini credential: {secret}")

    assert has_secret_pattern(bundle)


def test_secret_scanner_ignores_generated_temporary_test_directories(tmp_path: Path) -> None:
    generated = tmp_path / ".tmp" / "pytest-fixture" / "runtime.js"
    basetemp_generated = tmp_path / ".tmp-final-pytest" / "case" / "runtime.js"
    for item in (generated, basetemp_generated):
        item.parent.mkdir(parents=True)
        item.write_text("generated test artifact", encoding="utf-8")

    assert generated not in candidate_files([tmp_path])
    assert basetemp_generated not in candidate_files([tmp_path])
