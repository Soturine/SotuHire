from streamlit.testing.v1 import AppTest


def test_quick_mode_is_single_page_without_preferences_or_history_tabs():
    app = AppTest.from_file("app.py").run(timeout=30)

    assert not app.exception
    assert app.tabs == []
    assert any(button.label == "Rodar demo completa" for button in app.button)
    assert not any(expander.label == "Ajustar preferências" for expander in app.expander)


def test_advanced_mode_shows_complete_tool_tabs():
    app = AppTest.from_file("app.py").run(timeout=30)
    app = app.radio[0].set_value("Modo avançado").run(timeout=30)
    labels = [tab.label for tab in app.tabs]

    assert not app.exception
    assert "Preferências" in labels
    assert "Search Intelligence" in labels
    assert "Histórico" in labels
    assert "Dashboard" in labels
