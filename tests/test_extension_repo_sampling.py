from modules.portfolio.file_sampler import is_sampleable_path, prioritize_paths


def test_extension_repo_sampling_prioritizes_explanatory_files():
    sampled = prioritize_paths(
        [
            "assets/demo.mp4",
            "build/bundle.js",
            "README.md",
            "package.json",
            "Dockerfile",
            ".github/workflows/ci.yml",
            "src/app.ts",
            "tests/app.test.ts",
            "docs/architecture.md",
        ]
    )

    assert set(sampled[:3]) == {"README.md", "package.json", "Dockerfile"}
    assert ".github/workflows/ci.yml" in sampled
    assert "tests/app.test.ts" in sampled
    assert not is_sampleable_path("assets/demo.mp4")
    assert not is_sampleable_path("src/enormous.py", size_bytes=200_001)
