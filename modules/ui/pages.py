"""Page renderers for the guided SotuHire Streamlit workflow."""

from __future__ import annotations

import hashlib

import streamlit as st

from modules.ai.structured_analysis import StructuredAnalysisResult
from modules.exporters.analysis_exporter import (
    analysis_to_json,
    analysis_to_markdown,
    tailor_to_markdown,
)
from modules.parsers.job_description_parser import parse_job_description
from modules.parsers.resume_parser import parse_resume_file, parse_resume_text
from modules.schemas.job_posting import JobPostingSchema
from modules.schemas.resume_profile import ResumeProfileSchema
from modules.schemas.resume_tailor import ResumeTailorOutput
from modules.tracker.dashboard import calculate_dashboard_metrics
from modules.tracker.job_tracker import JobTracker
from modules.tracker.status import JobStatus
from modules.ui.components import (
    csv_items,
    display_value,
    line_items,
    modality_label,
    render_chips,
    render_data_card,
    render_item_cards,
    render_list,
    render_score_card,
    seniority_label,
)
from modules.ui.layout import (
    CONTRACTS,
    LEVELS,
    MODALITIES,
    initialize_state,
    render_header,
    render_sidebar,
    run_analysis,
)
from modules.ui.styles import inject_styles

TRACKER = JobTracker()


def _section_heading(kicker: str, title: str, caption: str) -> None:
    st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.subheader(title)
    st.caption(caption)


def _resume_review(profile: ResumeProfileSchema) -> None:
    st.markdown("#### Dados detectados")
    contact = st.columns(4)
    with contact[0]:
        render_data_card("Nome", profile.name)
    with contact[1]:
        render_data_card("Email", profile.email)
    with contact[2]:
        render_data_card("Telefone", profile.phone)
    with contact[3]:
        render_data_card("Localização", profile.city)

    st.markdown("**Links**")
    render_chips(profile.links, "Nenhum link detectado.")
    st.markdown("**Skills técnicas**")
    render_chips(profile.skills, "Nenhuma skill detectada.")
    if profile.soft_skills:
        st.markdown("**Soft skills**")
        render_chips(profile.soft_skills)
    if profile.languages:
        st.markdown("**Idiomas**")
        render_chips(profile.languages)

    summary = st.columns(3)
    summary[0].metric("Skills", len(profile.skills))
    summary[1].metric("Experiências", len(profile.experiences))
    summary[2].metric("Projetos", len(profile.projects))

    sections = st.tabs(["Resumo", "Formação", "Experiências", "Projetos"])
    with sections[0]:
        render_item_cards([profile.summary] if profile.summary else [], "Resumo não detectado.")
    with sections[1]:
        render_item_cards(profile.education, "Formação não detectada.")
    with sections[2]:
        render_item_cards(profile.experiences, "Experiência não detectada.")
    with sections[3]:
        render_item_cards(profile.projects, "Projeto não detectado.")

    with st.expander("Editar dados detectados"), st.form("resume_review"):
        left, right = st.columns(2)
        with left:
            name = st.text_input("Nome", profile.name)
            email = st.text_input("Email", profile.email)
            phone = st.text_input("Telefone", profile.phone)
            city = st.text_input("Localização", profile.city)
            summary_text = st.text_area("Resumo curto", profile.summary, height=100)
        with right:
            links = st.text_input("Links, separados por vírgula", ", ".join(profile.links))
            skills = st.text_input("Skills, separadas por vírgula", ", ".join(profile.skills))
            education = st.text_area("Formação, uma por linha", "\n".join(profile.education))
            experiences = st.text_area(
                "Experiências, uma por linha", "\n".join(profile.experiences)
            )
            projects = st.text_area("Projetos, um por linha", "\n".join(profile.projects))
        if st.form_submit_button("Salvar revisão", type="primary"):
            st.session_state.resume_profile = profile.model_copy(
                update={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "city": city,
                    "summary": summary_text,
                    "links": csv_items(links),
                    "skills": csv_items(skills),
                    "education": line_items(education),
                    "experiences": line_items(experiences),
                    "projects": line_items(projects),
                }
            )
            st.success("Revisão do currículo salva.")


def render_resume_step() -> None:
    """Render upload/paste and automatically process the first upload."""
    _section_heading(
        "PASSO 1",
        "Seu currículo",
        "Envie TXT, PDF ou DOCX. A primeira leitura do arquivo acontece automaticamente.",
    )
    uploaded = st.file_uploader("Arquivo do currículo", type=["txt", "pdf", "docx"])
    pasted_resume = st.text_area(
        "Ou cole o texto do currículo",
        value=st.session_state.resume_text if not uploaded else "",
        height=170,
        placeholder="Cole aqui quando não quiser enviar um arquivo.",
    )

    if uploaded:
        content = uploaded.getvalue()
        fingerprint = hashlib.sha256(content).hexdigest()
        if fingerprint != st.session_state.resume_upload_fingerprint:
            try:
                profile = parse_resume_file(uploaded.name, content)
                st.session_state.resume_profile = profile
                st.session_state.resume_text = profile.raw_text
                st.session_state.resume_upload_fingerprint = fingerprint
                st.success("Currículo processado automaticamente. Revise os dados abaixo.")
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))

    action_label = (
        "Reprocessar currículo" if st.session_state.resume_profile.raw_text else "Processar texto"
    )
    if st.button(action_label, type="primary", disabled=not (uploaded or pasted_resume.strip())):
        try:
            profile = (
                parse_resume_file(uploaded.name, uploaded.getvalue())
                if uploaded
                else parse_resume_text(pasted_resume)
            )
            st.session_state.resume_profile = profile
            st.session_state.resume_text = profile.raw_text
            st.success("Currículo processado. Revise os dados abaixo.")
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))

    if st.session_state.resume_profile.raw_text:
        _resume_review(st.session_state.resume_profile)


def _job_review(job: JobPostingSchema) -> None:
    st.markdown("#### Dados detectados")
    facts = st.columns(4)
    with facts[0]:
        render_data_card("Cargo", job.title)
    with facts[1]:
        render_data_card("Empresa", job.company)
    with facts[2]:
        render_data_card("Localização", job.location)
    with facts[3]:
        render_data_card("Modalidade", modality_label(job.modality))

    details = st.columns(3)
    with details[0]:
        render_data_card("Contrato", job.contract)
    with details[1]:
        render_data_card("Senioridade", seniority_label(job.seniority))
    with details[2]:
        salary = f"R$ {job.salary_min:,}".replace(",", ".") if job.salary_min else ""
        render_data_card("Salário inicial", salary)

    st.markdown("**Skills obrigatórias**")
    render_chips(job.required_skills, "Nenhuma skill obrigatória detectada.")
    st.markdown("**Skills desejáveis**")
    render_chips(job.desired_skills, "Nenhuma skill desejável detectada.")
    if job.benefits:
        st.markdown("**Benefícios**")
        render_chips(job.benefits)
    if job.risk_flags:
        st.warning("Revise estes dados: " + " ".join(job.risk_flags))

    with st.expander("Editar dados detectados"), st.form("job_review"):
        left, right = st.columns(2)
        with left:
            title = st.text_input("Cargo", job.title)
            company = st.text_input("Empresa", job.company)
            location = st.text_input("Localização", job.location)
            modality = st.selectbox(
                "Modalidade",
                ["unknown", *MODALITIES],
                index=["unknown", *MODALITIES].index(job.modality),
                format_func=modality_label,
            )
        with right:
            contract = st.selectbox(
                "Contrato",
                ["", *CONTRACTS],
                index=["", *CONTRACTS].index(job.contract) if job.contract in CONTRACTS else 0,
                format_func=display_value,
            )
            seniority = st.selectbox(
                "Senioridade",
                ["", *LEVELS],
                index=["", *LEVELS].index(job.seniority) if job.seniority in LEVELS else 0,
                format_func=seniority_label,
            )
            salary_min = st.number_input(
                "Salário mínimo detectado", min_value=0, value=job.salary_min or 0, step=500
            )
            required = st.text_input(
                "Skills obrigatórias, separadas por vírgula", ", ".join(job.required_skills)
            )
        if st.form_submit_button("Salvar revisão", type="primary"):
            st.session_state.job_posting = job.model_copy(
                update={
                    "title": title,
                    "company": company,
                    "location": location,
                    "modality": modality,
                    "contract": contract,
                    "seniority": seniority,
                    "salary_min": salary_min or None,
                    "required_skills": csv_items(required),
                }
            )
            st.success("Revisão da vaga salva.")


def render_job_step() -> None:
    """Render vacancy paste and automatically refresh detected fields."""
    _section_heading(
        "PASSO 2",
        "A vaga",
        "Cole a descrição. Cargo, modalidade, contrato, senioridade e skills serão sugeridos.",
    )
    vacancy_text = st.text_area(
        "Descrição completa da vaga",
        value=st.session_state.job_text,
        height=240,
        placeholder="Cole a descrição completa da oportunidade.",
    )
    if vacancy_text.strip() and vacancy_text != st.session_state.job_text:
        st.session_state.job_text = vacancy_text
        st.session_state.job_posting = parse_job_description(vacancy_text)
        st.success("Vaga processada automaticamente. Revise os dados abaixo.")
    if st.button("Reprocessar vaga", disabled=not vacancy_text.strip()):
        st.session_state.job_text = vacancy_text
        st.session_state.job_posting = parse_job_description(vacancy_text)
    if st.session_state.job_posting.raw_text:
        _job_review(st.session_state.job_posting)


def render_preferences_step(mode: str) -> None:
    """Render optional opportunity-fit preferences."""
    _section_heading(
        "PASSO 3",
        "Suas preferências",
        "Opcional no modo rápido. Use para personalizar o Opportunity Fit Score.",
    )
    with st.expander("Ajustar preferências", expanded=mode == "Modo avançado"):
        st.text_input(
            "Localizações preferidas",
            placeholder="São Paulo, Campinas",
            key="preferred_locations",
        )
        st.multiselect(
            "Modalidades preferidas",
            MODALITIES,
            key="preferred_modalities",
            format_func=modality_label,
        )
        st.number_input("Salário mínimo desejado", min_value=0, step=500, key="min_salary")
        st.multiselect("Contratos aceitos", CONTRACTS, key="accepted_contracts")
        st.multiselect(
            "Senioridades alvo", LEVELS, key="target_levels", format_func=seniority_label
        )
        st.text_input("Notas de prioridade", key="priority_notes")


def _render_result_content(result: StructuredAnalysisResult, tailor: ResumeTailorOutput) -> None:
    analysis = result.analysis
    cards = st.columns(4)
    render_score_card(
        cards[0], "Match Score", analysis.match_score, "Aderência às palavras da vaga."
    )
    render_score_card(cards[1], "ATS Score", analysis.ats_score, "Leitura provável por triagem.")
    render_score_card(
        cards[2],
        "Opportunity Fit",
        analysis.opportunity_fit_score,
        "Compatibilidade com preferências.",
    )
    render_score_card(cards[3], "Risk Score", analysis.risk_score, "Sinais que pedem revisão.")
    st.caption(f"Análise estruturada via {result.provider}.")
    if result.warning:
        st.warning(result.warning)

    tabs = st.tabs(
        [
            "Recomendação",
            "Pontos fortes",
            "Gaps",
            "Keywords",
            "Resume Tailor",
            "Mensagem",
            "Próximos passos",
            "Exportar",
        ]
    )
    with tabs[0]:
        recommendation = analysis.recommendation.replace("_", " ").title()
        (st.success if analysis.should_apply() else st.warning)(f"Recomendação: {recommendation}")
        render_list(analysis.risk_flags, "Nenhum risco adicional detectado.")
    with tabs[1]:
        render_list(analysis.strengths, "Nenhum ponto forte detectado.")
    with tabs[2]:
        render_list(analysis.gaps, "Nenhum gap prioritário.")
    with tabs[3]:
        render_chips(analysis.missing_keywords, "Nenhuma keyword prioritária ausente.")
    with tabs[4]:
        st.markdown("**Resumo profissional direcionado**")
        st.info(tailor.professional_summary or analysis.tailored_summary or "Sem resumo sugerido.")
        render_item_cards(tailor.improved_bullets, "Sem bullets sugeridos.")
        st.markdown("**Keywords seguras**")
        render_chips(tailor.keywords_added, "Nenhuma keyword segura adicional.")
    with tabs[5]:
        st.info(
            "O SotuHire não envia mensagens automaticamente. Use os pontos fortes e revise "
            "manualmente qualquer contato com recrutadores."
        )
    with tabs[6]:
        render_list(
            [
                "Confirme os dados detectados antes de usar a análise.",
                "Ajuste o currículo apenas com evidências reais.",
                "Pesquise a empresa e valide condições não informadas.",
            ],
            "",
        )
    with tabs[7]:
        exports = st.columns(3)
        exports[0].download_button(
            "Análise JSON",
            analysis_to_json(analysis),
            "sotuhire-analysis.json",
            "application/json",
            use_container_width=True,
        )
        exports[1].download_button(
            "Análise Markdown",
            analysis_to_markdown(analysis),
            "sotuhire-analysis.md",
            "text/markdown",
            use_container_width=True,
        )
        exports[2].download_button(
            "Resume Tailor",
            tailor_to_markdown(tailor),
            "sotuhire-resume-tailor.md",
            "text/markdown",
            use_container_width=True,
        )
        with st.expander("Salvar no histórico local"):
            st.info("O texto bruto do currículo e da vaga não é salvo.")
            acknowledged = st.checkbox("Entendi e quero salvar esta análise localmente.")
            notes = st.text_area("Notas opcionais", key="save_notes")
            if st.button("Salvar análise", disabled=not acknowledged):
                record = TRACKER.add_analysis(
                    analysis,
                    job_title=st.session_state.job_posting.title,
                    company=st.session_state.job_posting.company,
                    tailor=tailor,
                    notes=notes,
                    privacy_acknowledged=acknowledged,
                )
                st.success(f"Análise salva: {record.id[:8]}")


def render_results_step(provider_name: str) -> None:
    """Render the analysis action and structured result."""
    _section_heading(
        "PASSO 4",
        "Resultado",
        "Scores, evidências e próximos passos organizados para revisão humana.",
    )
    ready = bool(st.session_state.resume_text.strip() and st.session_state.job_text.strip())
    if not ready:
        st.info("Processe o currículo e a vaga para liberar a análise.")
    if st.button(
        "Analisar oportunidade",
        type="primary",
        use_container_width=True,
        disabled=not ready,
    ):
        with st.spinner("Analisando aderência, ATS, preferências e riscos..."):
            run_analysis(provider_name)
    if st.session_state.analysis_result and st.session_state.tailor_output:
        _render_result_content(st.session_state.analysis_result, st.session_state.tailor_output)


def render_history_step() -> None:
    """Render saved analyses and allow status changes."""
    _section_heading("HISTÓRICO", "Análises salvas", "Dados estruturados armazenados localmente.")
    records = TRACKER.list_analyses()
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
    scores = st.columns(4)
    scores[0].metric("Match", selected.analysis.match_score)
    scores[1].metric("ATS", selected.analysis.ats_score)
    scores[2].metric("Fit", selected.analysis.opportunity_fit_score)
    scores[3].metric("Risco", selected.analysis.risk_score)
    new_status = st.selectbox(
        "Status no tracker",
        [status.value for status in JobStatus],
        index=[status.value for status in JobStatus].index(selected.status.value),
    )
    if st.button("Atualizar status"):
        TRACKER.change_status(selected.id, new_status)
        st.success("Status atualizado.")
        st.rerun()


def render_dashboard_step() -> None:
    """Render local dashboard metrics."""
    _section_heading("DASHBOARD", "Visão geral da busca", "Acompanhamento das análises salvas.")
    metrics = calculate_dashboard_metrics(TRACKER.list_analyses())
    first = st.columns(3)
    first[0].metric("Vagas analisadas", metrics.total_analyzed)
    first[1].metric("Match médio", metrics.average_match_score)
    first[2].metric("ATS médio", metrics.average_ats_score)
    second = st.columns(3)
    second[0].metric("Opportunity Fit médio", metrics.average_opportunity_fit)
    second[1].metric("Recomendadas", metrics.recommended_to_apply)
    second[2].metric("Alto risco", metrics.high_risk)
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


def render_app() -> None:
    """Configure and render the complete guided application."""
    st.set_page_config(page_title="SotuHire v0.4.1", page_icon="S", layout="wide")
    initialize_state()
    inject_styles()
    render_header()
    mode, provider_name = render_sidebar()
    tabs = st.tabs(
        ["1. Currículo", "2. Vaga", "3. Preferências", "4. Resultado", "Histórico", "Dashboard"]
    )
    with tabs[0]:
        render_resume_step()
    with tabs[1]:
        render_job_step()
    with tabs[2]:
        render_preferences_step(mode)
    with tabs[3]:
        render_results_step(provider_name)
    with tabs[4]:
        render_history_step()
    with tabs[5]:
        render_dashboard_step()
    st.caption(
        "Processamento local por padrão · revisão humana obrigatória · sem auto-apply · "
        "sem invenção de experiência."
    )
