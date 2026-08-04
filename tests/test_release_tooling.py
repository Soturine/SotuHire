from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from scripts.build_sbom import build_sbom
from scripts.package_extension import RUNTIME_FILES, package_extension
from scripts.verify_extension_package import verify_package


def test_sbom_is_cyclonedx_and_deterministic() -> None:
    first = build_sbom()
    second = build_sbom()

    assert first == second
    assert first["bomFormat"] == "CycloneDX"
    assert first["metadata"]["component"]["version"] == "1.9.9"
    assert {item["name"] for item in first["components"]} >= {"fastapi", "pymupdf"}


def test_extension_package_verifier_accepts_release_payload(tmp_path: Path) -> None:
    package = package_extension(output=tmp_path / "extension.zip")

    manifest = verify_package(package)

    assert manifest["version"] == "0.9.5"


def test_extension_package_verifier_rejects_extra_entry(tmp_path: Path) -> None:
    valid = package_extension(output=tmp_path / "valid.zip")
    invalid = tmp_path / "invalid.zip"
    with ZipFile(valid) as source, ZipFile(invalid, "w", ZIP_DEFLATED) as target:
        for name in RUNTIME_FILES:
            target.writestr(name, source.read(name))
        target.writestr("unexpected.txt", json.dumps({"secret": False}))

    with pytest.raises(ValueError, match="Payload divergente"):
        verify_package(invalid)
