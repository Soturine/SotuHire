from streamlit.testing.v1 import AppTest


def test_advanced_collection_ui_is_available_without_network_call():
    app = AppTest.from_file("app.py").run(timeout=30)
    app = app.radio[0].set_value("Modo avançado").run(timeout=30)

    assert not app.exception
    assert any(tab.label == "Coletar vagas" for tab in app.tabs)
    assert any(button.label == "Coletar vagas" for button in app.button)
    assert any(button.label == "Salvar fonte" for button in app.button)
