"""Actionable Search Intelligence and Hidden Jobs Radar components."""

from __future__ import annotations

import streamlit as st

from modules.scraping import ScrapingSource, inspect_source_safety
from modules.scraping.collection import collect_public_source
from modules.search_intelligence.schemas import SourceSuggestion
from modules.ui.scraping_page import OPPORTUNITY_STORE, save_source, use_opportunity_for_analysis


def actionable_source(source: SourceSuggestion) -> ScrapingSource:
    """Convert a strategy suggestion into a collectable public source."""
    return ScrapingSource(
        name=source.name,
        type=source.source_type,
        url=source.url,
        enabled=True,
        max_items=20,
        delay_seconds=2.0,
        notes=source.reason,
    )


def render_actionable_source(
    source: SourceSuggestion,
    *,
    key_prefix: str,
    provider_name: str,
) -> None:
    """Render save, test, collect, and analyze actions for one source."""
    configured = actionable_source(source)
    safety = inspect_source_safety(source.url)
    with st.container(border=True):
        st.markdown(f"**[{source.name}]({source.url})** · {source.reason}")
        st.caption(
            f"Status: {source.status} · Tipo: {source.source_type} · "
            f"Segurança: {safety.robots_status}"
        )
        actions = st.columns(4)
        if actions[0].button("Salvar fonte", key=f"{key_prefix}_save"):
            st.success(f"Fonte salva em {save_source(configured)}.")
        if actions[1].button("Testar fonte", key=f"{key_prefix}_test", disabled=not safety.allowed):
            st.session_state[f"{key_prefix}_result"] = collect_public_source(
                configured, persist=False
            )
        if actions[2].button(
            "Coletar desta fonte",
            key=f"{key_prefix}_collect",
            disabled=not safety.allowed,
            type="primary",
        ):
            st.session_state[f"{key_prefix}_result"] = collect_public_source(configured)
        opportunities = OPPORTUNITY_STORE.list()
        if actions[3].button(
            "Analisar oportunidade",
            key=f"{key_prefix}_analyze",
            disabled=not opportunities,
        ):
            use_opportunity_for_analysis(0, provider_name)
            st.success("Primeira oportunidade coletada carregada para análise.")
        result = st.session_state.get(f"{key_prefix}_result")
        if result:
            if result.failures:
                st.error(result.failures[0])
            else:
                st.success(
                    f"Fonte coletada · {result.new_count} novas · "
                    f"{result.duplicate_count} duplicadas · {result.updated_count} atualizadas."
                )
