from modules.ui.advanced_mode import ADVANCED_TABS


def test_advanced_mode_contains_complete_workflow():
    assert ADVANCED_TABS == [
        "Currículo",
        "Vaga",
        "Preferências",
        "Resultado",
        "Coletar vagas",
        "Search Intelligence",
        "Memória de carreira",
        "Histórico",
        "Dashboard",
        "Exportações",
        "Configurações técnicas",
    ]
