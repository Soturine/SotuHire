"""Quick-mode presentation rules kept separate from the advanced workflow."""

from __future__ import annotations

QUICK_INPUT_HEIGHT = 110
QUICK_VISIBLE_SECTIONS = {
    "Currículo",
    "Vaga",
    "Resultado",
}
QUICK_HIDDEN_SECTIONS = {
    "Preferências",
    "Coletar vagas",
    "Search Intelligence",
    "Memória de carreira",
    "Histórico",
    "Dashboard",
    "Exportações",
    "Configurações técnicas",
}


def compact_status(label: str, value: str, count: int = 0) -> str:
    """Build a compact status line for processed quick-mode inputs."""
    detail = value.strip() or "dados detectados"
    suffix = f" · {count} skills" if count else ""
    return f"{label} pronto · {detail}{suffix}"
