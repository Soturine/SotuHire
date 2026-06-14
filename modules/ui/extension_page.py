"""Streamlit controls for the local assistive browser companion."""

from __future__ import annotations

import streamlit as st

from modules.local_api import (
    CaptureActionRequest,
    CompanionAnalysisContext,
    CompanionCaptureStore,
    LocalCompanionService,
    server_status,
    start_server,
    stop_server,
)
from modules.local_api.security import configured_token
from modules.parsers.job_description_parser import parse_job_description
from modules.ui.layout import build_preferences


def _sync_context(service: LocalCompanionService, provider_name: str) -> None:
    service.save_active_context(
        CompanionAnalysisContext(
            resume_text=str(st.session_state.get("resume_text", "")),
            preferences=build_preferences().model_dump(),
            provider=provider_name,
        )
    )


def render_extension_page(provider_name: str) -> None:
    """Render Local API status, installation help, and received captures."""
    service = LocalCompanionService()
    _sync_context(service, provider_name)
    status = server_status()

    st.subheader("Extensão assistiva")
    st.caption(
        "Capture a página que você abriu manualmente e envie para análise, memória e tracker."
    )
    status_columns = st.columns(3)
    status_columns[0].metric("Local API", "Ativa" if status["running"] else "Parada")
    status_columns[1].metric("Endpoint", f"{status['host']}:{status['port']}")
    status_columns[2].metric(
        "Token local", "Configurado" if configured_token() else "Não configurado"
    )

    actions = st.columns(2)
    if actions[0].button("Iniciar Local API", disabled=bool(status["running"])):
        start_server()
        st.rerun()
    if actions[1].button("Parar Local API", disabled=not bool(status["running"])):
        stop_server()
        st.rerun()

    with st.expander("Como instalar e usar a extensão", expanded=not bool(status["running"])):
        st.markdown(
            "1. Abra `chrome://extensions` e ative o modo do desenvolvedor.\n"
            "2. Escolha **Carregar sem compactação** e selecione `browser-extension/`.\n"
            "3. Inicie a Local API nesta aba.\n"
            "4. Abra uma vaga ou lista de candidaturas e use o popup do SotuHire.\n\n"
            "Para listas paginadas, use **Adicionar página ao lote** em cada página e depois "
            "**Enviar lote acumulado**."
        )
        st.info(
            "A extensão lê somente a página atual aberta pelo usuário. Ela não faz login, "
            "não guarda senha e não burla CAPTCHA."
        )

    captures = CompanionCaptureStore().list()
    st.markdown("### Últimas capturas recebidas")
    if not captures:
        st.info("Nenhuma captura recebida ainda.")
        return

    for record in captures[:30]:
        capture = record.capture
        with st.container(border=True):
            st.markdown(f"**{capture.job_title or capture.page_title or 'Vaga capturada'}**")
            st.caption(
                f"{capture.company or 'Empresa não detectada'} · {record.status} · "
                f"{capture.collection_method}"
            )
            st.caption(capture.url)
            buttons = st.columns(3)
            if buttons[0].button("Usar na análise", key=f"use_capture_{record.id}"):
                text = capture.description or capture.visible_text
                st.session_state.job_text = text
                st.session_state.job_posting = parse_job_description(text).model_copy(
                    update={
                        "title": capture.job_title or capture.page_title,
                        "company": capture.company,
                        "location": capture.location,
                    }
                )
                st.session_state.last_analysis_fingerprint = ""
                st.success("Vaga capturada aplicada à análise atual.")
            if buttons[1].button("Analisar captura", key=f"analyze_capture_{record.id}"):
                _sync_context(service, provider_name)
                response = service.analyze_capture(
                    CaptureActionRequest(capture_id=record.id, use_ai=provider_name == "gemini")
                )
                st.success(
                    f"Match {response.match_score} · ATS {response.ats_score} · "
                    f"{response.recommendation}"
                )
            if buttons[2].button("Salvar no tracker", key=f"track_capture_{record.id}"):
                _sync_context(service, provider_name)
                response = service.track_capture(
                    CaptureActionRequest(capture_id=record.id, use_ai=provider_name == "gemini")
                )
                st.success(f"Salva no tracker: {response.tracker_id[:8]}")
