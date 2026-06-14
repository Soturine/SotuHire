"""Streamlit workflow for public opportunity collection."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from modules.opportunities import OpportunityStore, filter_opportunities, opportunity_to_job_posting
from modules.scraping import ScrapingSource, inspect_source_safety
from modules.scraping.browser_session import (
    inspect_browser_session,
    launch_authenticated_browser,
)
from modules.scraping.collection import (
    capture_user_assisted_opportunity,
    collect_authenticated_source,
    collect_public_source,
)
from modules.scraping.connectors.configured_source import load_configured_sources
from modules.scraping.schemas import CollectionMode, ScrapedOpportunity
from modules.tracker.job_tracker import JobTracker
from modules.ui.layout import run_analysis

SOURCE_TYPES = {
    "URL de vaga": "manual_url",
    "URL de listagem": "generic_public_page",
    "RSS/Atom": "rss",
    "Página de carreira de empresa": "company_career_page",
}
COLLECTION_MODES: dict[str, CollectionMode] = {
    "Coleta pública automática": "PUBLIC_SCRAPING",
    "Coleta por URL": "MANUAL_URL",
    "Captura assistida pelo usuário": "USER_ASSISTED_CAPTURE",
    "Navegador autenticado autorizado": "AUTHENTICATED_BROWSER",
}
OPPORTUNITY_STORE = OpportunityStore()
TRACKER = JobTracker()


def save_source(source: ScrapingSource, path: str | Path = "config/sources.toml") -> Path:
    """Append one source to the local non-versioned TOML file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    escaped_name = source.name.replace('"', '\\"')
    escaped_url = source.url.replace('"', '\\"')
    escaped_cdp_url = source.browser_cdp_url.replace('"', '\\"')
    escaped_authorization = source.authorization_reference.replace('"', '\\"')
    block = "\n".join(
        [
            "[[sources]]",
            f'name = "{escaped_name}"',
            f'type = "{source.type}"',
            f'url = "{escaped_url}"',
            f'collection_mode = "{source.collection_mode}"',
            f"enabled = {str(source.enabled).lower()}",
            f"max_items = {source.max_items}",
            f"max_pages = {source.max_pages}",
            f"delay_seconds = {source.delay_seconds}",
            f'browser_cdp_url = "{escaped_cdp_url}"',
            f"authorized_use = {str(source.authorized_use).lower()}",
            f'authorization_reference = "{escaped_authorization}"',
            "",
        ]
    )
    with target.open("a", encoding="utf-8") as file:
        file.write(block + "\n")
    return target


def source_from_controls() -> ScrapingSource:
    """Build the selected source from current Streamlit state."""
    configured = load_configured_sources()
    mode = COLLECTION_MODES.get(
        st.session_state.get("collection_mode_label", "Coleta pública automática"),
        "PUBLIC_SCRAPING",
    )
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
        type="manual_url"
        if mode == "MANUAL_URL"
        else SOURCE_TYPES.get(input_type, safety.detected_type),
        url=url,
        collection_mode=mode,
        enabled=True,
        max_items=1
        if mode == "MANUAL_URL"
        else int(st.session_state.get("collection_max_items", 20)),
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


def use_opportunity(opportunity: ScrapedOpportunity, provider_name: str) -> None:
    """Load one explicit opportunity into the current analysis flow."""
    st.session_state.job_text = opportunity.description
    st.session_state.job_posting = opportunity_to_job_posting(opportunity)
    st.session_state.last_analysis_fingerprint = ""
    if st.session_state.resume_text.strip():
        run_analysis(provider_name)


def save_opportunity_to_tracker(opportunity: ScrapedOpportunity, provider_name: str) -> None:
    """Analyze one opportunity and persist the reviewed result in the tracker."""
    use_opportunity(opportunity, provider_name)
    result = st.session_state.get("analysis_result")
    if result is None:
        raise ValueError("Carregue um currículo antes de enviar a vaga para o tracker.")
    TRACKER.add_analysis(
        result.analysis,
        job_title=opportunity.title,
        company=opportunity.company or "",
        modality=opportunity.modality or "",
        seniority=opportunity.seniority or "",
        tailor=st.session_state.get("tailor_output"),
        notes=f"Capturada de {opportunity.source_url}",
        privacy_acknowledged=True,
    )


def render_user_assisted_capture(provider_name: str) -> None:
    """Render single-page capture controlled entirely by the user."""
    st.info(
        "Abra a vaga ou publicação no navegador, revise o conteúdo visível e cole somente "
        "a oportunidade atual. O SotuHire não acessa cookies, sessão ou outras páginas."
    )
    details = st.columns(2)
    source_url = details[0].text_input(
        "URL da página atual (opcional)",
        key="assisted_capture_url",
        placeholder="https://plataforma.example/vaga-atual",
    )
    title_hint = details[1].text_input("Título da vaga (opcional)", key="assisted_capture_title")
    text = st.text_area(
        "Conteúdo visível da vaga ou publicação atual",
        key="assisted_capture_text",
        height=220,
        placeholder="Cole apenas o conteúdo da oportunidade que está aberta no navegador.",
    )
    preview = capture_user_assisted_opportunity(
        text,
        source_url=source_url,
        title_hint=title_hint,
        persist=False,
    )
    if preview.opportunities:
        opportunity = preview.opportunities[0]
        st.markdown(f"**Preview:** {opportunity.title}")
        st.caption(
            f"{opportunity.company or 'Empresa não informada'} · "
            f"{opportunity.location or 'Local não informado'}"
        )
    actions = st.columns(3)
    if actions[0].button("Salvar vaga atual no SotuHire", type="primary", use_container_width=True):
        result = capture_user_assisted_opportunity(
            text,
            source_url=source_url,
            title_hint=title_hint,
        )
        st.session_state.assisted_capture_result = result
        (st.success if result.opportunities else st.error)(
            "Vaga atual salva no SotuHire." if result.opportunities else result.failures[0]
        )
    if actions[1].button(
        "Analisar vaga atual",
        use_container_width=True,
        disabled=not preview.opportunities,
    ):
        use_opportunity(preview.opportunities[0], provider_name)
        st.success("Vaga atual carregada para análise.")
    if actions[2].button(
        "Enviar para tracker",
        use_container_width=True,
        disabled=not preview.opportunities or not st.session_state.resume_text.strip(),
    ):
        save_opportunity_to_tracker(preview.opportunities[0], provider_name)
        st.success("Vaga atual analisada e enviada para o tracker.")


def authenticated_source_from_controls() -> ScrapingSource:
    """Build an authorized browser source from current Streamlit state."""
    url = str(st.session_state.get("authenticated_start_url", "")).strip()
    return ScrapingSource(
        name=str(st.session_state.get("authenticated_source_name", "")).strip()
        or "Navegador autenticado",
        type="authenticated_browser",
        url=url,
        collection_mode="AUTHENTICATED_BROWSER",
        enabled=True,
        max_items=int(st.session_state.get("authenticated_max_items", 50)),
        max_pages=int(st.session_state.get("authenticated_max_pages", 5)),
        delay_seconds=float(st.session_state.get("authenticated_delay", 2.0)),
        browser_cdp_url=str(
            st.session_state.get("authenticated_cdp_url", "http://127.0.0.1:9222")
        ).strip(),
        authorized_use=bool(st.session_state.get("authenticated_authorized_use", False)),
        authorization_reference=str(
            st.session_state.get("authenticated_authorization_reference", "")
        ).strip(),
    )


def render_authenticated_browser_collection() -> None:
    """Render authorized crawling controls for a previously authenticated browser."""
    st.info(
        "Conecta a um Chromium iniciado pelo usuário via CDP e usa a sessão já autenticada. "
        "O SotuHire abre abas próprias, navega vagas ou publicações e não automatiza o login."
    )
    identity = st.columns(2)
    identity[0].text_input("Nome da fonte", key="authenticated_source_name")
    identity[1].text_input(
        "Endpoint CDP do navegador",
        value="http://127.0.0.1:9222",
        key="authenticated_cdp_url",
    )
    st.text_input(
        "URL inicial autenticada",
        placeholder="https://www.linkedin.com/jobs/search/?keywords=python",
        key="authenticated_start_url",
    )
    limits = st.columns(3)
    limits[0].number_input("Limite de itens", 1, 1000, 50, key="authenticated_max_items")
    limits[1].number_input("Páginas/rolagens", 1, 50, 5, key="authenticated_max_pages")
    limits[2].number_input("Intervalo de navegação", 0.2, 60.0, 2.0, key="authenticated_delay")
    st.text_input(
        "Referência da autorização",
        placeholder="Responsável, documento ou finalidade autorizada",
        key="authenticated_authorization_reference",
    )
    st.checkbox(
        "Confirmo que esta conta e esta coleta estão autorizadas para uso automatizado.",
        key="authenticated_authorized_use",
    )
    source = authenticated_source_from_controls()
    session = inspect_browser_session(source.browser_cdp_url)
    if session.available:
        st.success(f"Conexão CDP pronta: {session.browser}")
    else:
        st.warning(
            "O Chrome aberto normalmente não expõe a conexão CDP. "
            "Abra o navegador dedicado abaixo, faça login manualmente nele e teste a conexão."
        )
    ready = bool(
        source.url and source.browser_cdp_url and source.authorized_use and session.available
    )
    browser_actions = st.columns(2)
    if browser_actions[0].button("Abrir navegador para login", use_container_width=True):
        try:
            status = launch_authenticated_browser(source.url, source.browser_cdp_url)
            (st.success if status.available else st.error)(status.message)
            if status.available:
                st.rerun()
        except Exception as exc:
            st.error(f"Não foi possível abrir o navegador: {exc}")
    if browser_actions[1].button("Testar conexão do navegador", use_container_width=True):
        status = inspect_browser_session(source.browser_cdp_url)
        (st.success if status.available else st.error)(status.message)
    actions = st.columns(2)
    if actions[0].button(
        "Coletar no navegador autenticado",
        type="primary",
        use_container_width=True,
        disabled=not ready,
    ):
        with st.spinner("Navegando na sessão autenticada..."):
            st.session_state.collection_result = collect_authenticated_source(source)
    if actions[1].button(
        "Salvar fonte autenticada",
        use_container_width=True,
        disabled=not ready,
    ):
        st.success(f"Fonte salva localmente em {save_source(source)}.")


def render_collection_results(provider_name: str) -> None:
    """Render the latest collection summary and locally stored opportunities."""
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
        st.info("Nenhuma coleta executada ainda. Escolha uma fonte para iniciar.")
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
            item_actions = st.columns(5)
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
                save_opportunity_to_tracker(opportunity, provider_name)
                st.success("Oportunidade salva no tracker.")
            if item_actions[4].button("Já me candidatei", key=f"applied_{index}"):
                TRACKER.add_existing_application(
                    job_title=opportunity.title,
                    company=opportunity.company or "",
                    source_url=opportunity.source_url,
                    notes=f"Candidatura informada manualmente. Fonte: {opportunity.source_url}",
                )
                st.success("Vaga registrada como candidatura já realizada.")


def render_scraping_page(provider_name: str) -> None:
    """Render collection controls and locally stored opportunities."""
    st.markdown("### Coletar ou capturar oportunidade")
    st.caption("Escolha explicitamente como o SotuHire deve receber oportunidades.")
    st.radio(
        "Modo de coleta",
        list(COLLECTION_MODES),
        horizontal=True,
        key="collection_mode_label",
    )
    mode = COLLECTION_MODES[st.session_state.collection_mode_label]
    if mode == "USER_ASSISTED_CAPTURE":
        render_user_assisted_capture(provider_name)
        return
    if mode == "AUTHENTICATED_BROWSER":
        render_authenticated_browser_collection()
        render_collection_results(provider_name)
        return
    if mode == "MANUAL_URL":
        st.info("Cole uma URL específica. O sistema coleta somente essa página e não segue links.")
    else:
        st.info("Coleta pública automática com cache, rate limit, limite de itens e robots.txt.")
    configured = load_configured_sources()
    controls = st.columns(2)
    input_options = (
        ["URL de vaga"]
        if mode == "MANUAL_URL"
        else ["URL de listagem", "RSS/Atom", "Página de carreira de empresa", "Fonte configurada"]
    )
    controls[0].selectbox("Tipo de entrada", input_options, key="collection_input_type")
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
    limits[0].number_input(
        "Limite por coleta",
        1,
        200,
        1 if mode == "MANUAL_URL" else 20,
        disabled=mode == "MANUAL_URL",
        key="collection_max_items",
    )
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

    render_collection_results(provider_name)
