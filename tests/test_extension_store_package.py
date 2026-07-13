import json
from zipfile import ZipFile

from scripts.package_extension import RUNTIME_FILES, package_extension, validate_extension


def test_extension_store_package_contains_only_valid_runtime_files(tmp_path):
    manifest = validate_extension()
    output = package_extension(output=tmp_path / "extension.zip")

    assert manifest["manifest_version"] == 3
    assert output.is_file()
    with ZipFile(output) as archive:
        assert set(archive.namelist()) == set(RUNTIME_FILES)
        packaged_manifest = json.loads(archive.read("manifest.json"))
    assert packaged_manifest["version"] == "0.9.2"
    assert "queue_runtime.js" in archive.namelist()
    assert not any(name.startswith(("store/", "tests/")) for name in RUNTIME_FILES)
