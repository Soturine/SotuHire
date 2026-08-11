from pathlib import Path


def test_readme_references_only_current_v2_product_visuals() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    screenshots = [
        Path("docs/assets/screenshots/sotuhire-v2-human-approved-career-copilot.gif"),
        Path("docs/assets/screenshots/v2/01-cockpit-light.png"),
        Path("docs/assets/screenshots/v2/03-copilot.png"),
        Path("docs/assets/screenshots/v2/04-approval-queue.png"),
        Path("docs/assets/screenshots/v2/05-evidence-inbox.png"),
        Path("docs/assets/screenshots/v2/08-portfolio.png"),
        Path("docs/assets/screenshots/v2/19-mobile-cockpit.png"),
        Path("docs/assets/screenshots/extension/popup-main.png"),
        Path("docs/assets/screenshots/extension/prepare-application-lab.png"),
    ]

    for screenshot in screenshots:
        assert screenshot.as_posix() in readme
        assert screenshot.exists()
        assert 10_000 < screenshot.stat().st_size < 2_000_000
    assert readme.count("docs/assets/screenshots/") == len(screenshots)
    assert "sotuhire-web-product-walkthrough.gif" not in readme
    assert "sotuhire-v1.9.9-document-to-application-walkthrough.gif" not in readme
    assert "sotuhire-v1.11.0" not in readme


def test_readme_is_a_complete_v2_product_entrypoint() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert readme.startswith(
        "# SotuHire — Copiloto de Carreira Local-First com IA, Evidências e Aprovação Humana"
    )
    for section in [
        "## Por que existe",
        "## A jornada em cinco minutos",
        "## Capacidades principais",
        "## Como tudo se conecta",
        "## Screenshots",
        "## Instalação",
        "## IA e providers",
        "## Privacidade e segurança",
        "## Migração e recuperação",
        "## Desenvolvimento, testes e documentação",
        "## Post-v2",
        "## Licença",
    ]:
        assert section in readme
    for link in [
        "docs/documentation-index.md",
        "docs/01-product/roadmap.md",
        "docs/02-architecture/evidence-graph.md",
        "docs/02-architecture/human-approved-copilot.md",
        "docs/06-engineering/v2-security-threat-model.md",
        "docs/releases/v2.0.md",
        "CHANGELOG.md",
        "browser-extension/README.md",
    ]:
        assert link in readme
