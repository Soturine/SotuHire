from pathlib import Path


def test_readme_references_only_current_v2_product_visuals() -> None:
    """The README shows the 2.1 build (scripts/capture_readme_media.py), nothing older."""
    readme = Path("README.md").read_text(encoding="utf-8")
    app = [
        "cockpit",
        "copilot",
        "profile",
        "resume-studio",
        "radar",
        "tracker",
        "application-lab",
        "approvals",
        "cockpit-dark",
        "mobile-cockpit",
    ]
    screenshots = [Path(f"docs/assets/screenshots/app/{name}.png") for name in app] + [
        Path("docs/assets/screenshots/extension/popup-main.png"),
        Path("docs/assets/screenshots/extension/github-analysis-modal.png"),
    ]

    for screenshot in screenshots:
        assert screenshot.as_posix() in readme
        assert screenshot.exists()
        assert 10_000 < screenshot.stat().st_size < 2_000_000
    assert readme.count("docs/assets/screenshots/") == len(screenshots)
    demo = Path("docs/assets/demo/sotuhire-demo.gif")
    assert demo.as_posix() in readme
    assert 100_000 < demo.stat().st_size < 3_000_000  # readable, still light for a README
    assert Path("docs/assets/demo/sotuhire-demo.webm").exists()
    assert "sotuhire-v2-human-approved-career-copilot.gif" not in readme
    assert "docs/assets/screenshots/v2/" not in readme
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
        "## Próximos passos",
        "## Licença",
    ]:
        assert section in readme
    for link in [
        "docs/documentation-index.md",
        "docs/01-product/roadmap.md",
        "docs/02-architecture/evidence-graph.md",
        "docs/02-architecture/human-approved-copilot.md",
        "docs/06-engineering/v2-security-threat-model.md",
        "docs/releases/v2.1.md",
        "docs/releases/v2.0.md",
        "CHANGELOG.md",
        "browser-extension/README.md",
    ]:
        assert link in readme
