"""Small presentation helpers shared by SotuHire pages."""

from __future__ import annotations

from html import escape
from typing import Any

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
PROVIDER_LABELS = {
    "gemini": "Gemini",
    "local": "Análise local",
    "mock": "Análise local",
}


def csv_items(value: str) -> list[str]:
    """Split comma-separated user edits into unique values."""
    return list(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))


def line_items(value: str) -> list[str]:
    """Split newline-separated user edits into unique values."""
    return list(dict.fromkeys(item.strip(" -*•\t") for item in value.splitlines() if item.strip()))


def block_items(value: str) -> list[str]:
    """Split blank-line-separated user edits while preserving multiline blocks."""
    return list(
        dict.fromkeys(
            "\n".join(line.strip(" -*•\t") for line in block.splitlines() if line.strip())
            for block in value.split("\n\n")
            if block.strip()
        )
    )


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


def provider_label(value: str) -> str:
    """Translate an internal provider name for presentation."""
    return PROVIDER_LABELS.get(value, display_value(value))


def render_chips(items: list[str], empty_message: str = "Nenhum item detectado.") -> None:
    """Render escaped items as compact chips."""
    if not items:
        st.caption(empty_message)
        return
    chips = "".join(f'<span class="chip">{escape(item)}</span>' for item in items)
    st.markdown(chips, unsafe_allow_html=True)


def link_label(url: str) -> str:
    """Return a compact human label for a detected resume link."""
    lowered = url.lower()
    if "linkedin.com" in lowered:
        return "LinkedIn"
    if "github.com" in lowered:
        return "GitHub"
    if any(domain in lowered for domain in ["behance.net", "vercel.app", "netlify.app", "github.io"]):
        return "Portfólio"
    return "Site"


def link_href(url: str) -> str:
    """Add a safe web scheme to links detected without one."""
    return url if url.lower().startswith(("http://", "https://")) else f"https://{url}"


def render_links(items: list[str], empty_message: str = "Nenhum link detectado.") -> None:
    """Render detected links as compact clickable labels."""
    if not items:
        st.caption(empty_message)
        return
    links = "".join(
        f'<a class="chip" href="{escape(link_href(item), quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{escape(link_label(item))}</a>'
        for item in items
    )
    st.markdown(links, unsafe_allow_html=True)


def render_data_card(label: str, value: object) -> None:
    """Render one compact escaped fact card."""
    st.markdown(
        f'<div class="data-card"><small>{escape(label)}</small>'
        f"<strong>{escape(display_value(value))}</strong></div>",
        unsafe_allow_html=True,
    )


def _render_card(item: str) -> None:
    content = escape(item).replace("\n", "<br>")
    st.markdown(f'<div class="data-card">{content}</div>', unsafe_allow_html=True)


def render_item_cards(items: list[str], empty_message: str, visible_limit: int = 3) -> None:
    """Render a compact preview and put long lists behind an expander."""
    if not items:
        st.caption(empty_message)
        return
    for item in items[:visible_limit]:
        _render_card(item)
    if len(items) > visible_limit:
        with st.expander(f"Ver todos ({len(items)})"):
            for item in items[visible_limit:]:
                _render_card(item)


def render_list(items: list[str], empty_message: str) -> None:
    """Render a readable native list."""
    if not items:
        st.caption(empty_message)
        return
    for item in items:
        st.markdown(f"- {item}")


def render_score_card(column: Any, label: str, score: int, note: str) -> None:
    """Render a metric plus its short explanation."""
    column.metric(label, f"{score}/100")
    column.markdown(f'<div class="score-note">{escape(note)}</div>', unsafe_allow_html=True)
