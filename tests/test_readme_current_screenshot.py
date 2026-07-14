from pathlib import Path


def test_readme_is_atemporal_and_references_current_product_screenshots():
    readme = Path("README.md").read_text(encoding="utf-8")
    screenshots = [
        Path("docs/assets/screenshots/sotuhire-web-product-walkthrough.gif"),
        Path("docs/assets/screenshots/sotuhire-web-profile.png"),
        Path("docs/assets/screenshots/sotuhire-web-match.png"),
        Path("docs/assets/screenshots/sotuhire-web-radar-schedules.png"),
        Path("docs/assets/screenshots/sotuhire-web-tracker.png"),
        Path("docs/assets/screenshots/sotuhire-web-profile-lattes.png"),
        Path("docs/assets/screenshots/sotuhire-web-public-exams.png"),
        Path("docs/assets/screenshots/sotuhire-web-settings-ai.png"),
        Path("docs/assets/screenshots/sotuhire-web-privacy.png"),
        Path("docs/assets/screenshots/extension/popup-main.png"),
        Path("docs/assets/screenshots/extension/github-analysis-modal.png"),
    ]

    for screenshot in screenshots:
        assert str(screenshot).replace("\\", "/") in readme
        assert screenshot.exists()
        assert 10_000 < screenshot.stat().st_size < 2_000_000
    assert readme.count("docs/assets/screenshots/") == len(screenshots)
    assert "[CHANGELOG](CHANGELOG.md)" in readme
    assert "release-v1.9.7" in readme
    assert "Frontend moderno v1.9.0" not in readme
    assert "API local v1.9.0" not in readme
    assert "Na v1.8.2" not in readme
    for link in [
        "docs/documentation-index.md",
        "docs/01-product/roadmap.md",
        "docs/01-product/vision.md",
        "docs/01-product/multi-domain-product-strategy.md",
        "docs/02-architecture/module-integration-map.md",
        "docs/02-architecture/career-context-engine.md",
        "docs/02-architecture/extension-profile-bridge.md",
        "docs/02-architecture/integration-capability-matrix.md",
        "docs/02-architecture/storage-repository-architecture.md",
        "docs/02-architecture/sqlite-schema-and-migrations.md",
        "docs/02-architecture/application-snapshots.md",
        "docs/02-architecture/backup-restore-and-data-health.md",
        "docs/04-ai/prompt-catalog.md",
        "docs/04-ai/career-memory-rag.md",
        "docs/04-ai/ai-evaluation-plan.md",
        "docs/06-engineering/security-privacy.md",
        "docs/09-testing/golden-datasets.md",
        "docs/05-data-sources/job-sources.md",
        "docs/releases/v1.9.7.md",
        "CHANGELOG.md",
        "browser-extension/README.md",
        "apps/web/README.md",
    ]:
        assert link in readme

    required_sections = [
        "## Visão geral",
        "## Para quem serve",
        "## O que o SotuHire faz",
        "## Como as partes se conectam",
        "## Preview",
        "## Modos de uso",
        "## Instalação",
        "## Como executar",
        "## Configuração de IA",
        "## Qualidade e avaliação da IA",
        "## Extensão",
        "## Dados e privacidade",
        "## Arquitetura",
        "## Documentação",
        "## Roadmap",
        "## Contribuição",
        "## Licença",
    ]
    assert all(section in readme for section in required_sections)
    assert readme.count("v1.9.7") == 6  # badge URL/text and technical footer links only
