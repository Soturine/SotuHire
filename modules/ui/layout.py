"""Application layout, state, and workflow orchestration helpers."""

from __future__ import annotations

import streamlit as st

from modules.ai.structured_analysis import analyze_structured, gemini_setup_warning, get_provider
from modules.resume_tailor.tailor_rules import build_safe_tailor_output
from modules.schemas.job_posting import JobPostingSchema
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.user_preferences import UserPreferences
from modules.ui.components import csv_items

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
          <span class="version-pill">v0.4.2</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, str]:
    """Render friendly controls and return mode/provider selections."""
    with st.sidebar:
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
        provider_label = st.selectbox("Como analisar", provider_options, index=default_index)
        if provider_label == "Gemini":
            warning = gemini_setup_warning()
            if warning:
                st.warning(warning)
            else:
                st.caption("Gemini configurado. O currículo será enviado para análise externa.")
        else:
            st.caption("Análise determinística feita localmente, sem API.")
        st.divider()
        st.markdown("**Privacidade e responsabilidade**")
        st.caption("Currículos não são enviados para IA externa sem configuração explícita.")
        st.caption("O histórico local só é salvo após sua confirmação.")
        st.caption("Revisão humana obrigatória. O SotuHire não inventa dados.")
        return mode, PROVIDERS[provider_label]


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
