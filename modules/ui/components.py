"""Small presentation helpers shared by SotuHire pages."""

from __future__ import annotations

from html import escape

import streamlit as st

MODALITY_LABELS = {
    "remote": "Remoto",
    "hybrid": "Híbrido",
    "onsite": "Presencial",
    "unknown": "Não informado",
    "": "Não informado",
}
SENIORITY_LABELS = {
    "estagio": "Estágio",
    "trainee": "Trainee",
    "junior": "Júnior",
    "pleno": "Pleno",
    "senior": "Sênior",
    "lead": "Liderança",
    "especialista": "Especialista",
    "": "Não informado",
}


def csv_items(value: str) -> list[str]:
    """Split comma-separated user edits into unique values."""
    return list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


def line_items(value: str) -> list[str]:
    """Split newline-separated user edits into unique values."""
    return list(dict.fromkeys(item.strip(" -*•\t") for item in value.splitlines() if item.strip()))


def display_value(value: object) -> str:
    """Return a friendly Portuguese label for missing values."""
    if value is None or str(value).strip().lower() in {"", "unknown", "none"}:
        return "Não informado"
    return str(value)


def modality_label(value: str) -> str:
    """Translate the internal modality value for presentation."""
    return MODALITY_LABELS.get(value, display_value(value))


def seniority_label(value: str) -> str:
    """Translate the internal seniority value for presentation."""
    return SENIORITY_LABELS.get(value, display_value(value))


def render_chips(items: list[str], empty_message: str = "Nenhum item detectado.") -> None:
    """Render escaped items as compact chips."""
    if not items:
        st.caption(empty_message)
        return
    chips = "".join(f'<span class="chip">{escape(item)}</span>' for item in items)
    st.markdown(chips, unsafe_allow_html=True)


def render_data_card(label: str, value: object) -> None:
    """Render one compact escaped fact card."""
    st.markdown(
        f'<div class="data-card"><small>{escape(label)}</small>'
        f"<strong>{escape(display_value(value))}</strong></div>",
        unsafe_allow_html=True,
    )


def render_item_cards(items: list[str], empty_message: str) -> None:
    """Render list entries as individual cards."""
    if not items:
        st.caption(empty_message)
        return
    for item in items:
        st.markdown(
            f'<div class="data-card">{escape(item)}</div>',
            unsafe_allow_html=True,
        )


def render_list(items: list[str], empty_message: str) -> None:
    """Render a readable native list."""
    if not items:
        st.caption(empty_message)
        return
    for item in items:
        st.markdown(f"- {item}")


def render_score_card(column: object, label: str, score: int, note: str) -> None:
    """Render a metric plus its short explanation."""
    column.metric(label, f"{score}/100")
    column.markdown(f'<div class="score-note">{escape(note)}</div>', unsafe_allow_html=True)
