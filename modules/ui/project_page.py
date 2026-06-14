"""Streamlit page for GitHub, repository, project, and portfolio analysis."""

from __future__ import annotations

import streamlit as st

from modules.core.text_utils import normalize_text
from modules.local_api import LocalCompanionService
from modules.memory import CareerMemory
from modules.portfolio import ProjectAnalysisPayload, ProjectAnalysisStore


def _render_report(report) -> None:
    scores = st.columns(5)
    scores[0].metric("Nota geral", report.overall_score)
    scores[1].metric("Grade", report.grade)
    scores[2].metric("Repositório", report.repository_quality_score)
    scores[3].metric("Documentação", report.documentation_score)
    scores[4].metric("Commits", report.commit_quality_score)
    second = st.columns(5)
    second[0].metric("Perfil GitHub", report.github_profile_score)
    second[1].metric("Portfólio", report.portfolio_score)
    second[2].metric("Arquitetura", report.architecture_signal_score)
    second[3].metric("Profundidade", report.technical_depth_score)
    second[4].metric("Evidência ATS", report.ats_job_evidence_score)
    st.info(report.summary)
    st.markdown("**Stack detectada**")
    st.write(", ".join(report.stack) or "Nenhuma stack detectada.")
    columns = st.columns(2)
    with columns[0]:
        st.markdown("**Pontos fortes**")
        for item in report.strengths:
            st.success(item)
    with columns[1]:
        st.markdown("**Prioridades de melhoria**")
        for item in report.priority_recommendations:
            st.warning(item)
    with st.expander("Arquivos e commits analisados"):
        st.write(report.files_sampled)
        st.write(report.commit_analysis.relevant_messages)
    actions = st.columns(3)
    if actions[0].button("Usar como evidência", key=f"project_evidence_{report.id}"):
        CareerMemory().remember_project_analysis(report)
        st.success("Projeto enviado para a memória de carreira.")
    if actions[1].button("Comparar com vaga atual", key=f"project_compare_{report.id}"):
        job_text = normalize_text(str(st.session_state.get("job_text", "")))
        matches = [
            keyword for keyword in report.technical_keywords if normalize_text(keyword) in job_text
        ]
        st.info(
            f"{len(matches)} tecnologias do projeto aparecem na vaga atual: "
            + (", ".join(matches) or "nenhuma detectada")
        )
    if actions[2].button("Enviar para perfil profissional", key=f"project_profile_{report.id}"):
        CareerMemory().remember_project_analysis(report)
        st.success("Projeto disponível para o próximo recálculo do perfil profissional.")


def render_project_page() -> None:
    """Render manual and extension-connected project analysis workflows."""
    st.subheader("GitHub / Portfólio / Projetos")
    st.caption("Analise páginas públicas, salve evidências e reutilize sinais técnicos nas vagas.")
    with st.expander("Analisar novo projeto"), st.form("project_analysis_form"):
        top = st.columns(2)
        url = top[0].text_input("URL pública do perfil, repositório ou portfólio")
        page_type = top[1].selectbox(
            "Tipo",
            ["github_repo", "github_profile", "portfolio", "project"],
        )
        title = st.text_input("Título do projeto")
        visible_text = st.text_area("Conteúdo público visível", height=120)
        readme = st.text_area("README principal", height=150)
        files = st.text_area("Arquivos, um por linha", height=100)
        commits = st.text_area("Commits recentes, um por linha", height=100)
        languages = st.text_input("Linguagens, separadas por vírgula")
        topics = st.text_input("Topics, separados por vírgula")
        submitted = st.form_submit_button("Analisar e salvar como evidência", type="primary")
    if submitted:
        payload = ProjectAnalysisPayload(
            url=url,
            title=title,
            page_type=page_type,
            visible_text=visible_text,
            readme_text=readme,
            files_sampled=[line.strip() for line in files.splitlines() if line.strip()],
            commit_messages=[line.strip() for line in commits.splitlines() if line.strip()],
            languages=[item.strip() for item in languages.split(",") if item.strip()],
            topics=[item.strip() for item in topics.split(",") if item.strip()],
        )
        response = LocalCompanionService().analyze_project_capture(payload)
        st.session_state.latest_project_report = response.report
        st.success("Projeto analisado e enviado para a memória de carreira.")

    latest = st.session_state.get("latest_project_report")
    if latest:
        _render_report(latest)

    st.markdown("### Projetos salvos")
    records = ProjectAnalysisStore().list()
    if not records:
        st.info("Nenhum projeto salvo ainda. A extensão também pode enviar análises para esta aba.")
    for record in reversed(records[-20:]):
        with st.expander(
            f"{record.report.title} · {record.report.overall_score}/100 · {record.report.grade}"
        ):
            _render_report(record.report)
