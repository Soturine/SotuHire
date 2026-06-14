from modules.ui.quick_mode import QUICK_HIDDEN_SECTIONS, QUICK_INPUT_HEIGHT, QUICK_VISIBLE_SECTIONS


def test_quick_mode_contract_is_compact_and_hides_advanced_tools():
    assert QUICK_INPUT_HEIGHT <= 120
    assert {"Currículo", "Vaga", "Resultado"} == QUICK_VISIBLE_SECTIONS
    assert {
        "Dashboard",
        "Histórico",
        "Search Intelligence",
        "Extensão",
        "GitHub / Portfólio / Projetos",
    } <= QUICK_HIDDEN_SECTIONS
