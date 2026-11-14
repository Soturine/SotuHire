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
    assert first["metadata"]["component"]["version"] == "2.0.0"
    assert {item["name"] for item in first["components"]} >= {
        "fastapi",
        "pypdf",
        "reportlab",
    }


def test_sbom_covers_transitive_dependencies_and_verifies() -> None:
    import json
    import tomllib

    from scripts.build_sbom import PACKAGE_LOCK, PYPROJECT
    from scripts.verify_sbom import verify_sbom

    sbom = build_sbom()
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    names = {item["name"] for item in sbom["components"]}

    # Transitive, not declared by SotuHire: starlette (via fastapi), a nested npm package.
    assert "starlette" in names
    assert "pydantic-core" in names
    assert verify_sbom(sbom, project=project, lock=lock) == []


@pytest.mark.parametrize(
    ("absent", "expected_ok"),
    [("google-genai", True), ("fastapi", False)],
)
def test_sbom_completeness_depends_on_runtime_requirements_only(
    monkeypatch: pytest.MonkeyPatch, absent: str, expected_ok: bool
) -> None:
    """A dev-only install (no ``ai`` extra) is complete; a missing runtime dep is not."""
    import json
    import tomllib
    from importlib import metadata

    import scripts.build_sbom as builder
    from scripts.verify_sbom import verify_sbom

    real = metadata.distribution

    def distribution(name: str):
        if builder.canonicalize_name(name) == absent:
            raise metadata.PackageNotFoundError(name)
        return real(name)

    monkeypatch.setattr(builder.metadata, "distribution", distribution)
    sbom = builder.build_sbom()
    properties = {item["name"]: item["value"] for item in sbom["metadata"]["properties"]}
    errors = verify_sbom(
        sbom,
        project=tomllib.loads(builder.PYPROJECT.read_text(encoding="utf-8")),
        lock=json.loads(builder.PACKAGE_LOCK.read_text(encoding="utf-8")),
    )

    assert absent in properties["sotuhire:sbom:python-not-installed"].split(",")
    assert (errors == []) is expected_ok


def test_sbom_verifier_rejects_version_drift_and_missing_lock_entries() -> None:
    import json
    import tomllib

    from scripts.build_sbom import PACKAGE_LOCK, PYPROJECT
    from scripts.verify_sbom import verify_sbom

    sbom = build_sbom()
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    sbom["metadata"]["component"]["version"] = "1.11.0"
    sbom["components"] = [
        item for item in sbom["components"] if not item["purl"].startswith("pkg:npm/react@")
    ]

    errors = verify_sbom(sbom, project=project, lock=lock)

    assert any("1.11.0" in error for error in errors)
    assert any("pkg:npm/react@" in error for error in errors)


def test_extension_package_verifier_accepts_release_payload(tmp_path: Path) -> None:
    package = package_extension(output=tmp_path / "extension.zip")

    manifest = verify_package(package)

    assert manifest["version"] == "0.10.0"


def test_extension_package_verifier_rejects_extra_entry(tmp_path: Path) -> None:
    valid = package_extension(output=tmp_path / "valid.zip")
    invalid = tmp_path / "invalid.zip"
    with ZipFile(valid) as source, ZipFile(invalid, "w", ZIP_DEFLATED) as target:
        for name in RUNTIME_FILES:
            target.writestr(name, source.read(name))
        target.writestr("unexpected.txt", json.dumps({"secret": False}))

    with pytest.raises(ValueError, match="Payload divergente"):
        verify_package(invalid)
