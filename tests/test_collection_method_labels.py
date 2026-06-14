from modules.ui.components import collection_method_label


def test_browser_assisted_collection_method_has_friendly_label():
    assert collection_method_label("browser_assisted_capture") == "Extensão / captura assistida"
