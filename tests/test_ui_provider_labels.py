from modules.ui.components import link_href, link_label, provider_label
from modules.ui.layout import PROVIDERS


def test_ui_uses_friendly_provider_labels():
    assert provider_label("local") == "Análise local"
    assert provider_label("mock") == "Análise local"
    assert provider_label("gemini") == "Gemini"
    assert PROVIDERS == {"Análise local": "local", "Gemini": "gemini"}


def test_resume_links_use_clickable_compact_labels():
    assert link_label("linkedin.com/in/pessoa-exemplo") == "LinkedIn"
    assert link_label("github.com/pessoa-exemplo") == "GitHub"
    assert link_label("www.pessoa-exemplo.dev") == "Site"
    assert link_href("github.com/pessoa-exemplo") == "https://github.com/pessoa-exemplo"
