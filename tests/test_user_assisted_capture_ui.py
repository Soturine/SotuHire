from streamlit.testing.v1 import AppTest


def test_user_assisted_capture_ui_has_explicit_current_page_actions():
    app = AppTest.from_file("app.py").run(timeout=30)
    app = app.radio[0].set_value("Modo avançado").run(timeout=30)
    collection_mode = next(radio for radio in app.radio if radio.label == "Modo de coleta")
    app = collection_mode.set_value("Captura assistida pelo usuário").run(timeout=30)
    labels = [button.label for button in app.button]

    assert not app.exception
    assert "Salvar vaga atual no SotuHire" in labels
    assert "Analisar vaga atual" in labels
    assert "Enviar para tracker" in labels
    assert "Coletar vagas" not in labels
