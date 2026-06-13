"""Application layout, state, and workflow orchestration helpers."""

from __future__ import annotations

import hashlib

import streamlit as st

from modules.ai.setup import (
    gemini_api_key,
    gemini_setup_status,
    save_local_ai_config,
    test_gemini_connection,
)
from modules.ai.structured_analysis import analyze_structured, gemini_setup_warning, get_provider
from modules.examples import load_default_job_example, load_default_resume_example
from modules.parsers.job_description_parser import parse_job_description
from modules.parsers.resume_parser import parse_resume_text
from modules.resume_tailor.tailor_rules import build_safe_tailor_output
from modules.schemas.job_posting import JobPostingSchema
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.user_preferences import UserPreferences
from modules.ui.components import csv_items, provider_label

MODALITIES = ["remote", "hybrid", "onsite"]
CONTRACTS = ["CLT", "PJ", "estagio", "trainee", "temporario", "freelance"]
LEVELS = ["estagio", "trainee", "junior", "pleno", "senior", "lead"]
PROVIDERS = {
    "Análise local": "local",
    "Gemini": "gemini",
}


def initialize_state() -> None:
    """Create stable session defaults used across pages."""
    defaults: dict[str, object] = {
        "resume_text": "",
        "job_text": "",
        "resume_profile": ResumeProfileSchema(),
        "job_posting": JobPostingSchema(),
        "analysis_result": None,
        "tailor_output": None,
        "resume_upload_fingerprint": "",
        "last_analysis_fingerprint": "",
        "ai_setup_test_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header() -> None:
    """Render a compact product header."""
    st.markdown(
        """
        <div class="product-header">
          <div>
            <h1>SotuHire</h1>
            <p>Currículo, vaga e decisão em um fluxo revisável.</p>
          </div>
          <span class="version-pill">v0.5.0</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str]:
    """Render friendly controls and return mode/provider selections."""
    with st.sidebar:
        if st.session_state.pop("activate_gemini_after_save", False):
            st.session_state.provider_selection = "Gemini"
        st.title("Sua análise")
        st.caption("Escolha o nível de detalhe. O processamento local é o padrão.")
        mode = st.radio(
            "Experiência",
            ["Modo rápido", "Modo avançado"],
            help="O modo rápido usa padrões. O avançado libera preferências opcionais.",
        )
        provider_options = list(PROVIDERS)
        default_provider = get_provider().name
        default_index = next(
            (
                index
                for index, label in enumerate(provider_options)
                if PROVIDERS[label] == default_provider
            ),
            0,
        )
        provider_selection = st.selectbox(
            "Como analisar",
            provider_options,
            index=default_index,
            key="provider_selection",
        )
        if provider_selection == "Gemini":
            warning = gemini_setup_warning()
            if warning:
                st.warning(warning)
            else:
                st.caption("Gemini configurado. O currículo será enviado para análise externa.")
        else:
            st.caption("Análise determinística feita localmente, sem API.")
        with st.expander("Configurar IA"):
            result = st.session_state.analysis_result
            actual_provider = provider_label(result.provider) if result else "Ainda não executado"
            status = gemini_setup_status()
            st.caption(f"Selecionado: {provider_selection}")
            st.caption(f"Usado na última análise: {actual_provider}")
            if result:
                st.caption(
                    "Troca automática para análise local: sim"
                    if result.fallback_used
                    else "Troca automática para análise local: não"
                )
            st.caption(
                "Gemini key: configurada" if status.key_configured else "Gemini key: ausente"
            )
            st.caption("SDK Gemini: instalado" if status.sdk_installed else "SDK Gemini: ausente")
            status_message = (
                "Gemini configurado e ativo."
                if status.available and provider_selection == "Gemini"
                else status.message
            )
            (st.success if status.available else st.warning)(
                status_message
                if not status.reason
                else f"{status_message} Motivo: {status.reason}."
            )
            st.link_button(
                "Abrir Google AI Studio",
                "https://aistudio.google.com/app/apikey",
                use_container_width=True,
            )
            api_key = st.text_input(
                "GEMINI_API_KEY",
                value=gemini_api_key(),
                type="password",
                help="A chave fica apenas neste computador e não deve ser commitada.",
            )
            setup_actions = st.columns(2)
            if setup_actions[0].button("Testar Gemini", use_container_width=True):
                st.session_state.ai_setup_test_result = test_gemini_connection(api_key)
            if setup_actions[1].button("Salvar configuração local", use_container_width=True):
                try:
                    target = save_local_ai_config(api_key)
                    st.session_state.activate_gemini_after_save = True
                    st.session_state.ai_setup_saved_path = str(target)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if st.session_state.get("ai_setup_saved_path"):
                st.success(
                    "Gemini ativado. Configuração salva localmente em "
                    f"{st.session_state.ai_setup_saved_path}."
                )
            if st.session_state.ai_setup_test_result:
                test_result = st.session_state.ai_setup_test_result
                (st.success if test_result.success else st.error)(test_result.message)
                if test_result.detail:
                    with st.expander("Detalhes técnicos"):
                        st.code(test_result.detail)
        st.divider()
        st.markdown("**Privacidade e responsabilidade**")
        st.caption("Currículos não são enviados para IA externa sem configuração explícita.")
        st.caption("O histórico local só é salvo após sua confirmação.")
        st.caption("Revisão humana obrigatória. O SotuHire não inventa dados.")
        return mode, PROVIDERS[provider_selection]


def build_preferences() -> UserPreferences:
    """Build validated preferences from optional widgets."""
    return UserPreferences(
        preferred_locations=csv_items(st.session_state.get("preferred_locations", "")),
        preferred_modalities=st.session_state.get("preferred_modalities", []),
        min_salary=st.session_state.get("min_salary", 0) or None,
        accepted_contracts=st.session_state.get("accepted_contracts", []),
        target_levels=st.session_state.get("target_levels", []),
        priority_notes=csv_items(st.session_state.get("priority_notes", "")),
    )


def job_details(job: JobPostingSchema) -> dict[str, object]:
    """Convert reviewed job facts to the deterministic scoring contract."""
    return {
        "location": job.location or None,
        "modality": None if job.modality == "unknown" else job.modality,
        "salary_min": job.salary_min,
        "contract": job.contract or None,
        "seniority": job.seniority or None,
    }


def run_analysis(provider_name: str) -> None:
    """Run structured analysis and safe tailoring from reviewed inputs."""
    job = st.session_state.job_posting
    st.session_state.analysis_result = analyze_structured(
        st.session_state.resume_text,
        st.session_state.job_text,
        build_preferences(),
        job_details(job),
        provider=get_provider(provider_name),
    )
    st.session_state.tailor_output = build_safe_tailor_output(
        target_role=job.title or "Cargo alvo",
        target_company=job.company or None,
        job_text=st.session_state.job_text,
        evidence_text=st.session_state.resume_text,
    )
    st.session_state.last_analysis_fingerprint = analysis_fingerprint(provider_name)


def analysis_fingerprint(provider_name: str) -> str:
    """Return a stable fingerprint for automatic quick-mode analysis."""
    payload = "\0".join(
        [
            st.session_state.resume_text,
            st.session_state.job_text,
            provider_name,
            build_preferences().model_dump_json(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def should_run_quick_analysis(mode: str, provider_name: str) -> bool:
    """Return whether changed complete inputs need an automatic analysis."""
    ready = bool(st.session_state.resume_text.strip() and st.session_state.job_text.strip())
    return (
        mode == "Modo rápido"
        and ready
        and analysis_fingerprint(provider_name) != st.session_state.last_analysis_fingerprint
    )


def load_example_flow() -> None:
    """Load and parse the default fictitious resume and vacancy."""
    resume_text = load_default_resume_example()
    job_text = load_default_job_example()
    st.session_state.resume_text = resume_text
    st.session_state.resume_profile = parse_resume_text(resume_text)
    st.session_state.job_text = job_text
    st.session_state.job_posting = parse_job_description(job_text)
    st.session_state.last_analysis_fingerprint = ""
