from streamlit.testing.v1 import AppTest


def test_advanced_mode_exposes_memory_management():
    app = AppTest.from_file("app.py").run(timeout=30)
    app = app.radio[0].set_value("Modo avançado").run(timeout=30)
    labels = [tab.label for tab in app.tabs]
    buttons = [button.label for button in app.button]

    assert not app.exception
    assert "Memória de carreira" in labels
    assert "Exportar memória" in buttons
    assert "Apagar memória local" in buttons
