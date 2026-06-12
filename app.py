"""Streamlit interface for the SotuHire v0.1 deterministic MVP."""

from __future__ import annotations

import streamlit as st
from modules.analyzer.job_analyzer import analyze_job
from modules.resume_tailor.tailor_rules import build_safe_tailor_output
from modules.schemas.user_preferences import UserPreferences

MODALITIES = ["remote", "hybrid", "onsite"]
CONTRACTS = ["CLT", "PJ", "estagio", "temporario", "freelance"]
LEVELS = ["estagio", "trainee", "junior", "pleno", "senior", "lead"]


def split_csv(value: str) -> list[str]:
    """Split a comma-separated UI value into clean items."""
    return [item.strip() for item in value.split(",") if item.strip()]


def show_items(title: str, items: list[str], empty_message: str) -> None:
    """Render a titled list with a friendly empty state."""
    st.subheader(title)
    if not items:
        st.caption(empty_message)
        return
    for item in items:
        st.markdown(f"- {item}")


def main() -> None:
    """Render the SotuHire MVP interface."""
    st.set_page_config(page_title="SotuHire v0.1", layout="wide")
    st.title("SotuHire v0.1 — MVP Core")
    st.write(
        "Copiloto de carreira para analisar currículo, vaga, ATS, prioridades pessoais "
        "e estratégia de candidatura."
    )
    st.warning(
        "O Resume Tailor trabalha em modo sugestão: não invente experiências, resultados, "
        "certificados ou competências. Revise tudo antes de usar."
    )

    uploaded_resume = st.file_uploader("Ou envie o currículo em TXT", type=["txt"])
    uploaded_text = ""
    if uploaded_resume is not None:
        uploaded_text = uploaded_resume.getvalue().decode("utf-8", errors="replace")

    resume_text = st.text_area(
        "Currículo",
        value=uploaded_text,
        height=280,
        placeholder="Cole aqui o texto do seu currículo...",
    )
    job_text = st.text_area(
        "Descrição da vaga",
        height=280,
        placeholder="Cole aqui a descrição completa da vaga...",
    )

    st.subheader("Preferências e dados da oportunidade")
    preference_column, job_column = st.columns(2)

    with preference_column:
        st.markdown("**Suas preferências**")
        preferred_locations = split_csv(
            st.text_input("Localizações preferidas", placeholder="São Paulo, Campinas")
        )
        preferred_modalities = st.multiselect("Modalidades preferidas", MODALITIES)
        min_salary = st.number_input("Salário mínimo desejado", min_value=0, value=0, step=500)
        accepted_contracts = st.multiselect("Contratos aceitos", CONTRACTS)
        target_levels = st.multiselect("Senioridades alvo", LEVELS)
        priority_notes = split_csv(
            st.text_input("Notas de prioridade", placeholder="flexibilidade, plano de saúde")
        )

    with job_column:
        st.markdown("**Dados informados pela vaga**")
        target_role = st.text_input("Cargo alvo", placeholder="Analista de Dados Júnior")
        target_company = st.text_input("Empresa", placeholder="Empresa opcional")
        job_location = st.text_input("Localização da vaga", placeholder="São Paulo")
        job_modality = st.selectbox("Modalidade da vaga", ["unknown", *MODALITIES])
        job_salary = st.number_input("Salário mínimo divulgado", min_value=0, value=0, step=500)
        job_contract = st.selectbox("Contrato da vaga", ["unknown", *CONTRACTS])
        job_level = st.selectbox("Senioridade da vaga", ["unknown", *LEVELS])

    if not st.button("Analisar oportunidade", type="primary", use_container_width=True):
        return

    if not resume_text.strip() or not job_text.strip():
        st.error("Informe o texto do currículo e a descrição da vaga para executar a análise.")
        return

    preferences = UserPreferences(
        preferred_locations=preferred_locations,
        preferred_modalities=preferred_modalities,
        min_salary=min_salary or None,
        accepted_contracts=accepted_contracts,
        target_levels=target_levels,
        priority_notes=priority_notes,
    )
    job_details = {
        "location": job_location or None,
        "modality": None if job_modality == "unknown" else job_modality,
        "salary_min": job_salary or None,
        "contract": None if job_contract == "unknown" else job_contract,
        "seniority": None if job_level == "unknown" else job_level,
    }
    analysis = analyze_job(resume_text, job_text, preferences, job_details)
    tailor = build_safe_tailor_output(
        target_role=target_role.strip() or "Cargo alvo",
        target_company=target_company.strip() or None,
        job_text=job_text,
        evidence_text=resume_text,
    )

    st.divider()
    match_card, ats_card, fit_card, risk_card = st.columns(4)
    match_card.metric("Match Score", f"{analysis.match_score}/100")
    ats_card.metric("ATS Score", f"{analysis.ats_score}/100")
    fit_card.metric("Opportunity Fit", f"{analysis.opportunity_fit_score}/100")
    risk_card.metric("Risk Score", f"{analysis.risk_score}/100")

    st.subheader("Recomendação")
    st.success(analysis.recommendation.replace("_", " ").title())

    strengths_column, gaps_column = st.columns(2)
    with strengths_column:
        show_items("Pontos fortes", analysis.strengths, "Nenhum ponto forte identificado.")
    with gaps_column:
        show_items("Gaps", analysis.gaps, "Nenhum gap prioritário identificado.")

    show_items(
        "Palavras-chave ausentes",
        analysis.missing_keywords,
        "Nenhuma palavra-chave prioritária ausente.",
    )

    st.subheader("Resumo direcionado")
    if analysis.tailored_summary:
        st.info(analysis.tailored_summary)
    else:
        st.caption("Não foi possível sugerir resumo com as evidências fornecidas.")

    show_items("Avisos de risco", analysis.risk_flags, "Nenhum risco simples identificado.")
    show_items(
        "Keywords seguras para destacar",
        tailor.keywords_added,
        "Nenhuma keyword adicional apoiada pelas evidências.",
    )
    show_items(
        "Avisos do Resume Tailor",
        tailor.warnings,
        "Nenhum aviso do Resume Tailor.",
    )
    st.caption(
        "Revisão humana obrigatória. O SotuHire não faz auto-apply, não burla CAPTCHA "
        "e não adiciona informação sem evidência."
    )


if __name__ == "__main__":
    main()
