"""Guided Streamlit product interface for SotuHire v0.4."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv
from modules.ai.structured_analysis import (
    StructuredAnalysisResult,
    analyze_structured,
    get_provider,
)
from modules.exporters.analysis_exporter import (
    analysis_to_json,
    analysis_to_markdown,
    tailor_to_markdown,
)
from modules.parsers.job_description_parser import parse_job_description
from modules.parsers.resume_parser import parse_resume_file, parse_resume_text
from modules.resume_tailor.tailor_rules import build_safe_tailor_output
from modules.schemas.job_posting import JobPostingSchema
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.schemas.user_preferences import UserPreferences
from modules.tracker.dashboard import calculate_dashboard_metrics
from modules.tracker.job_tracker import JobTracker
from modules.tracker.status import JobStatus

load_dotenv()

MODALITIES = ["remote", "hybrid", "onsite"]
CONTRACTS = ["CLT", "PJ", "estagio", "temporario", "freelance"]
LEVELS = ["estagio", "trainee", "junior", "pleno", "senior", "lead"]
TRACKER = JobTracker()


def initialize_state() -> None:
    """Create stable session defaults used across tabs."""
    defaults: dict[str, object] = {
        "resume_text": "",
        "job_text": "",
        "resume_profile": ResumeProfileSchema(),
        "job_posting": JobPostingSchema(),
        "analysis_result": None,
        "tailor_output": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_css() -> None:
    """Apply a small product-like visual layer without coupling business rules."""
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%); }
        .hero { padding: 1.4rem 1.6rem; border-radius: 18px; color: white;
                background: linear-gradient(120deg, #172554, #4338ca 65%, #7c3aed); }
        .hero h1 { margin: 0; font-size: 2.1rem; }
        .hero p { margin: .55rem 0 0; color: #e0e7ff; }
        .soft-card { background: white; border: 1px solid #e2e8f0; border-radius: 14px;
                     padding: 1rem; box-shadow: 0 8px 24px rgba(15, 23, 42, .06); }
        .step { color: #4338ca; font-weight: 700; letter-spacing: .04em; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def csv_items(value: str) -> list[str]:
    """Split comma-separated user edits."""
    return [item.strip() for item in value.split(",") if item.strip()]


def show_items(title: str, items: list[str], empty_message: str) -> None:
    """Render a titled, compact list."""
    st.markdown(f"**{title}**")
    if not items:
        st.caption(empty_message)
        return
    for item in items:
        st.markdown(f"- {item}")


def show_resume_review(profile: ResumeProfileSchema) -> None:
    """Allow the user to review and edit detected resume fields."""
    with st.expander("Dados detectados do currículo", expanded=True):
        with st.form("resume_review"):
            name = st.text_input("Nome detectado", profile.name)
            summary = st.text_area("Resumo detectado", profile.summary, height=100)
            skills = st.text_input("Skills detectadas", ", ".join(profile.skills))
            links = st.text_input("Links detectados", ", ".join(profile.links))
            if st.form_submit_button("Confirmar dados do currículo"):
                st.session_state.resume_profile = profile.model_copy(
                    update={
                        "name": name,
                        "summary": summary,
                        "skills": csv_items(skills),
                        "links": csv_items(links),
                    }
                )
                st.success("Dados do currículo revisados.")
        summary_columns = st.columns(3)
        summary_columns[0].metric("Skills", len(profile.skills))
        summary_columns[1].metric("Experiências", len(profile.experiences))
        summary_columns[2].metric("Projetos", len(profile.projects))


def show_job_review(job: JobPostingSchema) -> None:
    """Allow the user to review and edit detected vacancy fields."""
    with st.expander("Dados detectados da vaga", expanded=True), st.form("job_review"):
        left, right = st.columns(2)
        with left:
            title = st.text_input("Cargo", job.title)
            company = st.text_input("Empresa", job.company)
            location = st.text_input("Localização", job.location)
            modality = st.selectbox(
                "Modalidade",
                ["unknown", *MODALITIES],
                index=["unknown", *MODALITIES].index(job.modality),
            )
        with right:
            contract = st.text_input("Contrato", job.contract)
            seniority = st.text_input("Senioridade", job.seniority)
            salary_min = st.number_input(
                "Salário mínimo detectado",
                min_value=0,
                value=job.salary_min or 0,
                step=500,
            )
            required_skills = st.text_input(
                "Skills obrigatórias",
                ", ".join(job.required_skills),
            )
        if st.form_submit_button("Confirmar dados da vaga"):
            st.session_state.job_posting = job.model_copy(
                update={
                    "title": title,
                    "company": company,
                    "location": location,
                    "modality": modality,
                    "contract": contract,
                    "seniority": seniority,
                    "salary_min": salary_min or None,
                    "required_skills": csv_items(required_skills),
                }
            )
            st.success("Dados da vaga revisados.")


def build_preferences() -> UserPreferences:
    """Build validated preferences from sidebar/advanced widgets."""
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
    result = analyze_structured(
        st.session_state.resume_text,
        st.session_state.job_text,
        build_preferences(),
        job_details(job),
        provider=get_provider(provider_name),
    )
    st.session_state.analysis_result = result
    st.session_state.tailor_output = build_safe_tailor_output(
        target_role=job.title or "Cargo alvo",
        target_company=job.company or None,
        job_text=st.session_state.job_text,
        evidence_text=st.session_state.resume_text,
    )


def show_score_cards(result: StructuredAnalysisResult) -> None:
    """Render the four core scores and provider metadata."""
    analysis = result.analysis
    columns = st.columns(4)
    columns[0].metric("Match Score", f"{analysis.match_score}/100")
    columns[1].metric("ATS Score", f"{analysis.ats_score}/100")
    columns[2].metric("Opportunity Fit", f"{analysis.opportunity_fit_score}/100")
    columns[3].metric("Risk Score", f"{analysis.risk_score}/100")
    st.caption(f"Análise estruturada via `{result.provider}`.")
    if result.warning:
        st.warning(result.warning)


def show_result(result: StructuredAnalysisResult, tailor: ResumeTailorOutput) -> None:
    """Render analysis, tailoring, exports, and save controls."""
    analysis = result.analysis
    show_score_cards(result)
    recommendation_style = st.success if analysis.should_apply() else st.warning
    recommendation_style(f"Recomendação: {analysis.recommendation.replace('_', ' ').title()}")

    left, right = st.columns(2)
    with left:
        show_items("Pontos fortes", analysis.strengths, "Nenhum ponto forte detectado.")
        show_items("Keywords seguras", tailor.keywords_added, "Nenhuma keyword segura adicional.")
    with right:
        show_items("Gaps", analysis.gaps, "Nenhum gap prioritário.")
        show_items("Avisos", [*analysis.risk_flags, *tailor.warnings], "Nenhum aviso.")

    with st.expander("Resume Tailor seguro", expanded=True):
        st.markdown("**Resumo profissional direcionado**")
        st.info(tailor.professional_summary or analysis.tailored_summary or "Sem resumo sugerido.")
        show_items("Bullet points melhorados", tailor.improved_bullets, "Sem bullets sugeridos.")
        show_items("Evidências usadas", tailor.evidence_used, "Sem evidências selecionadas.")
        show_items("Ordem sugerida", tailor.section_order, "Sem ordem sugerida.")

    export_columns = st.columns(3)
    export_columns[0].download_button(
        "Baixar análise JSON",
        analysis_to_json(analysis),
        "sotuhire-analysis.json",
        "application/json",
        use_container_width=True,
    )
    export_columns[1].download_button(
        "Baixar análise Markdown",
        analysis_to_markdown(analysis),
        "sotuhire-analysis.md",
        "text/markdown",
        use_container_width=True,
    )
    export_columns[2].download_button(
        "Baixar Resume Tailor",
        tailor_to_markdown(tailor),
        "sotuhire-resume-tailor.md",
        "text/markdown",
        use_container_width=True,
    )

    with st.expander("Salvar no histórico local"):
        st.info(
            "O histórico salva scores, recomendação, cargo, empresa e sugestões. "
            "O texto bruto do currículo não é salvo."
        )
        privacy_acknowledged = st.checkbox("Entendi e quero salvar esta análise localmente.")
        notes = st.text_area("Notas opcionais", key="save_notes")
        if st.button("Salvar análise", disabled=not privacy_acknowledged):
            record = TRACKER.add_analysis(
                analysis,
                job_title=st.session_state.job_posting.title,
                company=st.session_state.job_posting.company,
                tailor=tailor,
                notes=notes,
                privacy_acknowledged=privacy_acknowledged,
            )
            st.success(f"Análise salva: {record.id[:8]}")


def show_history() -> None:
    """Render saved analyses and allow status changes."""
    records = TRACKER.list_analyses()
    st.markdown('<div class="step">HISTÓRICO LOCAL</div>', unsafe_allow_html=True)
    st.subheader("Análises salvas")
    if not records:
        st.info("Nenhuma análise salva ainda.")
        return

    labels = {
        record.id: f"{record.job_title or 'Cargo não informado'} · "
        f"{record.company or 'Empresa não informada'} · {record.created_at:%d/%m/%Y %H:%M}"
        for record in records
    }
    selected_id = st.selectbox("Abrir análise", list(labels), format_func=labels.get)
    selected = next(record for record in records if record.id == selected_id)
    columns = st.columns(4)
    columns[0].metric("Match", selected.analysis.match_score)
    columns[1].metric("ATS", selected.analysis.ats_score)
    columns[2].metric("Fit", selected.analysis.opportunity_fit_score)
    columns[3].metric("Risco", selected.analysis.risk_score)
    st.write(f"Recomendação: `{selected.analysis.recommendation}`")
    new_status = st.selectbox(
        "Status no tracker",
        [status.value for status in JobStatus],
        index=[status.value for status in JobStatus].index(selected.status.value),
    )
    if st.button("Atualizar status"):
        TRACKER.change_status(selected.id, new_status)
        st.success("Status atualizado.")
        st.rerun()


def show_dashboard() -> None:
    """Render the initial local dashboard."""
    metrics = calculate_dashboard_metrics(TRACKER.list_analyses())
    st.markdown('<div class="step">DASHBOARD</div>', unsafe_allow_html=True)
    st.subheader("Visão geral da busca")
    first = st.columns(3)
    first[0].metric("Vagas analisadas", metrics.total_analyzed)
    first[1].metric("Match médio", metrics.average_match_score)
    first[2].metric("ATS médio", metrics.average_ats_score)
    second = st.columns(3)
    second[0].metric("Opportunity Fit médio", metrics.average_opportunity_fit)
    second[1].metric("Recomendadas para aplicar", metrics.recommended_to_apply)
    second[2].metric("Alto risco", metrics.high_risk)

    st.subheader("Últimas análises")
    if not metrics.latest:
        st.caption("O dashboard será preenchido quando você salvar análises.")
        return
    st.dataframe(
        [
            {
                "Cargo": item.job_title,
                "Empresa": item.company,
                "Status": item.status.value,
                "Match": item.analysis.match_score,
                "ATS": item.analysis.ats_score,
                "Fit": item.analysis.opportunity_fit_score,
                "Risco": item.analysis.risk_score,
                "Data": item.created_at.strftime("%d/%m/%Y %H:%M"),
            }
            for item in metrics.latest
        ],
        use_container_width=True,
        hide_index=True,
    )


def main() -> None:
    """Render the guided SotuHire application."""
    st.set_page_config(page_title="SotuHire v0.4", layout="wide")
    initialize_state()
    inject_css()

    st.markdown(
        """
        <div class="hero">
          <h1>SotuHire v0.4</h1>
          <p>Suba o currículo, cole a vaga e receba uma análise revisável em poucos passos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    with st.sidebar:
        st.header("Configuração")
        mode = st.radio("Experiência", ["Modo rápido", "Modo avançado"])
        provider_name = st.selectbox("Análise estruturada", ["mock", "gemini"])
        st.caption("Gemini usa fallback local automático se a chave ou SDK não estiver disponível.")
        st.divider()
        st.markdown("**Princípios**")
        st.caption("Revisão humana obrigatória.")
        st.caption("Sem auto-apply, CAPTCHA bypass ou scraping agressivo.")

    resume_tab, job_tab, preferences_tab, result_tab, history_tab, dashboard_tab = st.tabs(
        ["1. Currículo", "2. Vaga", "3. Preferências", "4. Resultado", "Histórico", "Dashboard"]
    )

    with resume_tab:
        st.markdown('<div class="step">PASSO 1 · CURRÍCULO</div>', unsafe_allow_html=True)
        st.subheader("Envie seu currículo")
        st.caption("TXT, PDF e DOCX são processados localmente para criar uma revisão assistida.")
        uploaded = st.file_uploader("Arquivo do currículo", type=["txt", "pdf", "docx"])
        pasted_resume = st.text_area(
            "Ou cole o texto do currículo",
            value=st.session_state.resume_text,
            height=220,
        )
        if st.button("Detectar dados do currículo", type="primary"):
            try:
                if uploaded:
                    profile = parse_resume_file(uploaded.name, uploaded.getvalue())
                else:
                    profile = parse_resume_text(pasted_resume)
                st.session_state.resume_profile = profile
                st.session_state.resume_text = profile.raw_text
                st.success("Currículo processado. Revise os dados detectados abaixo.")
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
        if st.session_state.resume_profile.raw_text:
            show_resume_review(st.session_state.resume_profile)

    with job_tab:
        st.markdown('<div class="step">PASSO 2 · VAGA</div>', unsafe_allow_html=True)
        st.subheader("Cole a descrição da vaga")
        st.caption("Cargo, empresa, modalidade, salário, senioridade e skills serão sugeridos.")
        vacancy_text = st.text_area(
            "Descrição completa da vaga",
            value=st.session_state.job_text,
            height=300,
        )
        if st.button("Detectar dados da vaga", type="primary"):
            posting = parse_job_description(vacancy_text)
            st.session_state.job_posting = posting
            st.session_state.job_text = vacancy_text
            st.success("Vaga processada. Revise os dados detectados abaixo.")
        if st.session_state.job_posting.raw_text:
            show_job_review(st.session_state.job_posting)

    with preferences_tab:
        st.markdown('<div class="step">PASSO 3 · PREFERÊNCIAS</div>', unsafe_allow_html=True)
        st.subheader("O que torna uma oportunidade boa para você?")
        st.info(
            "No modo rápido, preferências são opcionais. Abra os detalhes apenas se quiser "
            "personalizar o Opportunity Fit Score."
        )
        with st.expander("Preferências avançadas", expanded=mode == "Modo avançado"):
            st.text_input(
                "Localizações preferidas",
                placeholder="São Paulo, Campinas",
                key="preferred_locations",
            )
            st.multiselect("Modalidades preferidas", MODALITIES, key="preferred_modalities")
            st.number_input("Salário mínimo desejado", min_value=0, step=500, key="min_salary")
            st.multiselect("Contratos aceitos", CONTRACTS, key="accepted_contracts")
            st.multiselect("Senioridades alvo", LEVELS, key="target_levels")
            st.text_input("Notas de prioridade", key="priority_notes")

    with result_tab:
        st.markdown('<div class="step">PASSO 4 · RESULTADO</div>', unsafe_allow_html=True)
        st.subheader("Análise estruturada e revisável")
        ready = bool(st.session_state.resume_text.strip() and st.session_state.job_text.strip())
        if not ready:
            st.info("Processe o currículo e a vaga para liberar a análise.")
        if st.button(
            "Analisar oportunidade",
            type="primary",
            use_container_width=True,
            disabled=not ready,
        ):
            with st.spinner("Analisando aderência, ATS, prioridades e riscos..."):
                run_analysis(provider_name)
        if st.session_state.analysis_result and st.session_state.tailor_output:
            show_result(st.session_state.analysis_result, st.session_state.tailor_output)

    with history_tab:
        show_history()

    with dashboard_tab:
        show_dashboard()

    st.caption(
        "SotuHire trabalha com revisão humana. Não inventa experiência, não faz auto-apply "
        "e não envia mensagens automaticamente."
    )


if __name__ == "__main__":
    main()
