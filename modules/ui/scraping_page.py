"""Streamlit workflow for public opportunity collection."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from modules.opportunities import OpportunityStore, filter_opportunities, opportunity_to_job_posting
from modules.scraping import ScrapingSource, inspect_source_safety
from modules.scraping.collection import collect_public_source
from modules.scraping.connectors.configured_source import load_configured_sources
from modules.tracker.job_tracker import JobTracker
from modules.ui.layout import run_analysis

SOURCE_TYPES = {
    "URL de vaga": "manual_url",
    "URL de listagem": "generic_public_page",
    "RSS/Atom": "rss",
    "Página de carreira de empresa": "company_career_page",
}
OPPORTUNITY_STORE = OpportunityStore()
TRACKER = JobTracker()


def save_source(source: ScrapingSource, path: str | Path = "config/sources.toml") -> Path:
    """Append one source to the local non-versioned TOML file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    escaped_name = source.name.replace('"', '\\"')
    escaped_url = source.url.replace('"', '\\"')
    block = "\n".join(
        [
            "[[sources]]",
            f'name = "{escaped_name}"',
            f'type = "{source.type}"',
            f'url = "{escaped_url}"',
            f"enabled = {str(source.enabled).lower()}",
            f"max_items = {source.max_items}",
            f"delay_seconds = {source.delay_seconds}",
            "",
        ]
    )
    with target.open("a", encoding="utf-8") as file:
        file.write(block + "\n")
    return target


def source_from_controls() -> ScrapingSource:
    """Build the selected source from current Streamlit state."""
    configured = load_configured_sources()
    input_type = st.session_state.get("collection_input_type", "URL de vaga")
    if input_type == "Fonte configurada" and configured:
        selected_name = st.session_state.get("configured_source_name", configured[0].name)
        return next(source for source in configured if source.name == selected_name)
    url = str(st.session_state.get("collection_url", "")).strip()
    safety = inspect_source_safety(url)
    return ScrapingSource(
        name=str(st.session_state.get("collection_source_name", "")).strip()
        or safety.domain
        or "Fonte pública",
        type=SOURCE_TYPES.get(input_type, safety.detected_type),
        url=url,
        enabled=True,
        max_items=int(st.session_state.get("collection_max_items", 20)),
        delay_seconds=float(st.session_state.get("collection_delay", 2.0)),
    )


def use_opportunity_for_analysis(index: int, provider_name: str) -> None:
    """Load a collected opportunity into the current analysis flow."""
    opportunity = OPPORTUNITY_STORE.list()[index]
    st.session_state.job_text = opportunity.description
    st.session_state.job_posting = opportunity_to_job_posting(opportunity)
    st.session_state.last_analysis_fingerprint = ""
    if st.session_state.resume_text.strip():
        run_analysis(provider_name)


def render_scraping_page(provider_name: str) -> None:
    """Render collection controls and locally stored opportunities."""
    st.markdown("### Coletar vaga ou fonte pública")
    st.caption("Coleta automática de páginas públicas com robots.txt, cache, limite e dedupe.")
    configured = load_configured_sources()
    controls = st.columns(2)
    controls[0].selectbox(
        "Tipo de entrada", [*SOURCE_TYPES, "Fonte configurada"], key="collection_input_type"
    )
    if st.session_state.collection_input_type == "Fonte configurada":
        if configured:
            controls[1].selectbox(
                "Fonte configurada",
                [source.name for source in configured],
                key="configured_source_name",
            )
        else:
            controls[1].info("Copie config/sources.example.toml para config/sources.toml.")
    else:
        controls[1].text_input("Nome da fonte", key="collection_source_name")
        st.text_input(
            "Cole aqui a URL pública",
            placeholder="https://empresa.example/careers",
            key="collection_url",
        )
    limits = st.columns(2)
    limits[0].number_input("Limite por coleta", 1, 200, 20, key="collection_max_items")
    limits[1].number_input("Intervalo por domínio", 0.2, 60.0, 2.0, key="collection_delay")

    source = source_from_controls()
    safety = inspect_source_safety(source.url)
    preview = st.columns(5)
    preview[0].metric("Tipo detectado", safety.detected_type)
    preview[1].metric("Domínio", safety.domain or "inválido")
    preview[2].metric("Robots/segurança", safety.robots_status)
    preview[3].metric("Cache", "Local · 6h")
    preview[4].metric("Limite", source.max_items)
    if safety.warning:
        st.warning(safety.warning)

    actions = st.columns(4)
    if actions[0].button("Detectar tipo", use_container_width=True):
        st.session_state.collection_input_type = next(
            (label for label, value in SOURCE_TYPES.items() if value == safety.detected_type),
            "URL de listagem",
        )
        st.rerun()
    if actions[1].button("Testar fonte", use_container_width=True, disabled=not safety.allowed):
        st.session_state.collection_result = collect_public_source(source, persist=False)
    if actions[2].button(
        "Coletar vagas", type="primary", use_container_width=True, disabled=not safety.allowed
    ):
        with st.spinner("Coletando fonte pública..."):
            st.session_state.collection_result = collect_public_source(source)
    if actions[3].button("Salvar fonte", use_container_width=True, disabled=not safety.allowed):
        st.success(f"Fonte salva localmente em {save_source(source)}.")

    result = st.session_state.get("collection_result")
    if result:
        summary = st.columns(4)
        summary[0].metric("Vagas novas", result.new_count)
        summary[1].metric("Duplicadas ignoradas", result.duplicate_count)
        summary[2].metric("Atualizadas", result.updated_count)
        summary[3].metric("Falhas", len(result.failures))
        for failure in result.failures:
            st.error(failure)

    opportunities = OPPORTUNITY_STORE.list()
    st.markdown("### Oportunidades coletadas")
    if not opportunities:
        st.info("Nenhuma coleta executada ainda. Escolha uma fonte pública para iniciar.")
        return
    filters = st.columns(2)
    query = filters[0].text_input("Filtrar oportunidades", key="opportunity_query")
    sources = sorted({item.source for item in opportunities})
    source_filter = filters[1].selectbox("Fonte", ["", *sources], key="opportunity_source_filter")
    filtered = filter_opportunities(opportunities, query=query, source=source_filter)
    for opportunity in filtered:
        index = opportunities.index(opportunity)
        with st.container(border=True):
            st.markdown(
                f"**{opportunity.title}** · {opportunity.company or 'Empresa não informada'}"
            )
            st.caption(f"{opportunity.source} · {opportunity.location or 'Local não informado'}")
            st.write(opportunity.description[:500])
            item_actions = st.columns(4)
            if item_actions[0].button("Analisar esta vaga", key=f"analyze_{index}"):
                use_opportunity_for_analysis(index, provider_name)
                st.success("Vaga carregada e análise preparada.")
            item_actions[1].link_button("Abrir fonte", opportunity.source_url)
            if item_actions[2].button("Comparar com currículo", key=f"compare_{index}"):
                use_opportunity_for_analysis(index, provider_name)
                st.success("Comparação concluída.")
            if item_actions[3].button(
                "Salvar no tracker",
                key=f"save_collected_{index}",
                disabled=st.session_state.get("analysis_result") is None,
            ):
                use_opportunity_for_analysis(index, provider_name)
                result = st.session_state.analysis_result
                TRACKER.add_analysis(
                    result.analysis,
                    job_title=opportunity.title,
                    company=opportunity.company or "",
                    modality=opportunity.modality or "",
                    seniority=opportunity.seniority or "",
                    tailor=st.session_state.get("tailor_output"),
                    notes=f"Coletada de {opportunity.source_url}",
                    privacy_acknowledged=True,
                )
                st.success("Oportunidade salva no tracker.")
