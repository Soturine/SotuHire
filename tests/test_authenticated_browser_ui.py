from streamlit.testing.v1 import AppTest


def test_authenticated_browser_ui_has_authorized_crawling_controls():
    app = AppTest.from_file("app.py").run(timeout=30)
    app = app.radio[0].set_value("Modo avançado").run(timeout=30)
    collection_mode = next(radio for radio in app.radio if radio.label == "Modo de coleta")
    app = collection_mode.set_value("Navegador autenticado autorizado").run(timeout=30)
    labels = [button.label for button in app.button]
    checkbox_labels = [checkbox.label for checkbox in app.checkbox]

    assert not app.exception
    assert "Coletar no navegador autenticado" in labels
    assert "Salvar fonte autenticada" in labels
    assert "Abrir navegador para login" in labels
    assert "Testar conexão do navegador" in labels
    assert any("autorizadas para uso automatizado" in label for label in checkbox_labels)
