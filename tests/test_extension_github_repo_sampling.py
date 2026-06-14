from modules.portfolio.file_sampler import is_sampleable_path, prioritize_paths


def test_repository_sampling_prioritizes_central_files_and_ignores_generated_assets():
    paths = [
        "dist/app.js",
        "node_modules/lib/index.js",
        "assets/banner.png",
        "src/service.py",
        "tests/test_service.py",
        ".github/workflows/ci.yml",
        "README.md",
        "pyproject.toml",
        "poetry.lock",
    ]

    sampled = prioritize_paths(paths)

    assert sampled[:2] == ["README.md", "pyproject.toml"]
    assert "src/service.py" in sampled
    assert "tests/test_service.py" in sampled
    assert not any("node_modules" in path or path.endswith((".png", ".lock")) for path in sampled)
    assert not is_sampleable_path("src/huge.py", size_bytes=200_001)
