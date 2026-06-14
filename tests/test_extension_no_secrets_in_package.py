from zipfile import ZipFile

from scripts.package_extension import package_extension


def test_extension_zip_has_no_env_private_key_or_real_api_key(tmp_path):
    output = package_extension(output=tmp_path / "extension.zip")

    with ZipFile(output) as archive:
        names = archive.namelist()
        text = "\n".join(
            archive.read(name).decode("utf-8")
            for name in names
            if name.endswith((".js", ".json", ".html", ".css"))
        )

    assert not any(name.endswith(".env") for name in names)
    assert "BEGIN PRIVATE KEY" not in text
    assert "AIzaSy" not in text
    assert "GEMINI_API_KEY=" not in text
