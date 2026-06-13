"""Page renderers for the guided SotuHire Streamlit workflow."""

from __future__ import annotations

import hashlib

import streamlit as st

from modules.ai.structured_analysis import StructuredAnalysisResult
from modules.examples import load_default_job_example, load_default_resume_example
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
from modules.search_intelligence import SearchStrategyInput, build_search_intelligence_plan
from modules.tracker.dashboard import calculate_dashboard_metrics, filter_dashboard_records
from modules.tracker.job_tracker import JobTracker
from modules.tracker.status import JobStatus
from modules.ui.components import (
    block_items,
    csv_items,
    display_value,
    line_items,
    modality_label,
    provider_label,
    render_chips,
    render_data_card,
    render_item_cards,
    render_limited_chips,
    render_links,
    render_list,
    render_score_card,
    risk_label,
    seniority_label,
)
from modules.ui.layout import (
    CONTRACTS,
    LEVELS,
    MODALITIES,
    initialize_state,
    load_example_flow,
    render_header,
    render_sidebar,
    run_analysis,
    should_run_quick_analysis,
)
from modules.ui.styles import inject_styles

TRACKER = JobTracker()


def _section_heading(kicker: str, title: str, caption: str) -> None:
    st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.subheader(title)
    st.caption(caption)


def _resume_review(profile: ResumeProfileSchema, *, advanced: bool = True) -> None:
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
    render_links(profile.links)
    st.markdown("**Skills técnicas**")
    render_limited_chips(profile.skills, "Nenhuma skill detectada.")
    if profile.soft_skills:
        st.markdown("**Soft skills**")
        render_chips(profile.soft_skills)
    if profile.languages:
        st.markdown("**Idiomas**")
        render_chips(profile.languages)

    first_summary = st.columns(3)
    first_summary[0].metric("Skills técnicas", len(profile.skills))
    first_summary[1].metric("Soft skills", len(profile.soft_skills))
    first_summary[2].metric("Links", len(profile.links))
    second_summary = st.columns(3)
    second_summary[0].metric("Experiências", len(profile.experiences))
    second_summary[1].metric("Projetos", len(profile.projects))
    second_summary[2].metric("Formação", len(profile.education))

    if not advanced:
        return

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
                "Experiências, separe blocos com uma linha vazia",
                "\n\n".join(profile.experiences),
            )
            projects = st.text_area(
                "Projetos, separe blocos com uma linha vazia", "\n\n".join(profile.projects)
            )
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
                    "experiences": block_items(experiences),
                    "projects": block_items(projects),
                }
            )
            st.success("Revisão do currículo salva.")


def render_resume_step(*, advanced: bool = True) -> None:
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
    if not uploaded and not pasted_resume.strip() and st.button("Carregar exemplo de currículo"):
        example = load_default_resume_example()
        st.session_state.resume_text = example
        st.session_state.resume_profile = parse_resume_text(example)
        st.rerun()

    if uploaded:
        content = uploaded.getvalue()
        fingerprint = hashlib.sha256(content).hexdigest()
        if fingerprint != st.session_state.resume_upload_fingerprint:
            try:
                profile = parse_resume_file(uploaded.name, content)
                st.session_state.resume_profile = profile
                st.session_state.resume_text = profile.raw_text
                st.session_state.resume_upload_fingerprint = fingerprint
                st.session_state.last_analysis_fingerprint = ""
                st.success("Currículo processado automaticamente. Revise os dados abaixo.")
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))

    if not uploaded and pasted_resume.strip() and pasted_resume != st.session_state.resume_text:
        st.session_state.resume_profile = parse_resume_text(pasted_resume)
        st.session_state.resume_text = pasted_resume
        st.session_state.last_analysis_fingerprint = ""
        st.success("Currículo processado automaticamente. Revise apenas se quiser.")

    action_label = (
        "Reprocessar currículo" if st.session_state.resume_profile.raw_text else "Processar texto"
    )
    if st.button(action_label, disabled=not (uploaded or pasted_resume.strip())):
        try:
            profile = (
                parse_resume_file(uploaded.name, uploaded.getvalue())
                if uploaded
                else parse_resume_text(pasted_resume)
            )
            st.session_state.resume_profile = profile
            st.session_state.resume_text = profile.raw_text
            st.session_state.last_analysis_fingerprint = ""
            st.success("Currículo processado. Revise os dados abaixo.")
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))

    if st.session_state.resume_profile.raw_text:
        _resume_review(st.session_state.resume_profile, advanced=advanced)


def _job_review(job: JobPostingSchema, *, advanced: bool = True) -> None:
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

    if not advanced:
        return

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


def render_job_step(*, advanced: bool = True) -> None:
    """Render vacancy paste and automatically refresh detected fields."""
    _section_heading(
        "PASSO 2",
        "A vaga",
        "Cole a descrição. Cargo, modalidade, contrato, senioridade e skills serão sugeridos.",
    )
    vacancy_text = (
        st.text_area(
            "Descrição completa da vaga",
            value=st.session_state.job_text,
            height=240,
            placeholder="Cole a descrição completa da oportunidade.",
        )
        or ""
    )
    if not vacancy_text.strip() and st.button("Usar vaga fictícia de exemplo"):
        example = load_default_job_example()
        st.session_state.job_text = example
        st.session_state.job_posting = parse_job_description(example)
        st.session_state.last_analysis_fingerprint = ""
        st.rerun()
    if vacancy_text.strip() and vacancy_text != st.session_state.job_text:
        st.session_state.job_text = vacancy_text
        st.session_state.job_posting = parse_job_description(vacancy_text)
        st.session_state.last_analysis_fingerprint = ""
        st.success("Vaga processada automaticamente. Revise os dados abaixo.")
    if st.button("Reprocessar vaga", disabled=not vacancy_text.strip()):
        st.session_state.job_text = vacancy_text
        st.session_state.job_posting = parse_job_description(vacancy_text)
        st.session_state.last_analysis_fingerprint = ""
    if st.session_state.job_posting.raw_text:
        _job_review(st.session_state.job_posting, advanced=advanced)


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


def _render_result_content(
    result: StructuredAnalysisResult, tailor: ResumeTailorOutput, *, advanced: bool = True
) -> None:
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
    if result.provider == "gemini":
        st.success("Usando Gemini para melhorar a análise.")
    else:
        st.info("Usando análise local no seu computador.")
    if result.warning:
        st.warning(result.warning)
    if advanced:
        with st.expander("Detalhes técnicos da análise"):
            st.caption(f"Provider solicitado: {provider_label(result.requested_provider)}")
            st.caption(f"Provider realmente usado: {provider_label(result.provider)}")
            st.caption(f"Fallback usado: {'sim' if result.fallback_used else 'não'}")
            if result.diagnostic:
                diagnostic = result.diagnostic
                st.caption(f"Código: {diagnostic.code or 'não informado'}")
                st.caption(f"Motivo resumido: {diagnostic.summary}")
                st.caption(f"Modelo usado: {diagnostic.model}")
                st.caption(f"SDK instalado: google-genai {diagnostic.sdk_version}")
                st.caption(f"Variável encontrada: {diagnostic.key_source}")
                st.caption(f"Tipo de chamada: {diagnostic.call_type}")
                if diagnostic.suggestion:
                    st.info(diagnostic.suggestion)
                if diagnostic.raw_error:
                    st.code(diagnostic.raw_error)

    if not advanced:
        recommendation = analysis.recommendation.replace("_", " ").title()
        (st.success if analysis.should_apply() else st.warning)(f"Recomendação: {recommendation}")
        quick_sections = st.columns(2)
        with quick_sections[0]:
            st.markdown("**Por que aplicar**")
            render_list(analysis.strengths, "Nenhum ponto forte detectado.")
        with quick_sections[1]:
            st.markdown("**O que ajustar**")
            render_list(analysis.gaps, "Nenhum ajuste prioritário.")
        st.markdown("**Keywords prioritárias**")
        render_limited_chips(analysis.missing_keywords, "Nenhuma keyword prioritária ausente.")
        return

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
                    modality=st.session_state.job_posting.modality,
                    seniority=st.session_state.job_posting.seniority,
                    tailor=tailor,
                    notes=notes,
                    privacy_acknowledged=acknowledged,
                )
                st.success(f"Análise salva: {record.id[:8]}")


def render_results_step(mode: str, provider_name: str) -> None:
    """Render the analysis action and structured result."""
    _section_heading(
        "PASSO 4",
        "Resultado",
        "Scores, evidências e próximos passos organizados para revisão humana.",
    )
    ready = bool(st.session_state.resume_text.strip() and st.session_state.job_text.strip())
    if not ready:
        st.info("Processe o currículo e a vaga para liberar a análise.")
        if st.button("Rodar análise de exemplo", use_container_width=True):
            load_example_flow()
            st.rerun()
    if should_run_quick_analysis(mode, provider_name):
        with st.spinner("Currículo e vaga prontos. Preparando sua análise..."):
            run_analysis(provider_name)
        st.success("Análise atualizada automaticamente.")
    if st.button(
        "Analisar agora" if mode == "Modo rápido" else "Rodar análise novamente",
        type="primary" if mode == "Modo rápido" else "secondary",
        use_container_width=True,
        disabled=not ready,
    ):
        with st.spinner("Analisando aderência, ATS, preferências e riscos..."):
            run_analysis(provider_name)
    if st.session_state.analysis_result and st.session_state.tailor_output:
        _render_result_content(
            st.session_state.analysis_result,
            st.session_state.tailor_output,
            advanced=mode == "Modo avançado",
        )


def render_quick_mode(provider_name: str) -> None:
    """Render the compact one-page quick analysis flow."""
    st.markdown(
        '<div class="mode-banner"><strong>Modo rápido</strong>'
        "<span>Envie o currículo, cole a vaga e receba a análise automaticamente.</span></div>",
        unsafe_allow_html=True,
    )
    inputs = st.columns(2, gap="large")
    with inputs[0]:
        render_resume_step(advanced=False)
    with inputs[1]:
        render_job_step(advanced=False)
    render_results_step("Modo rápido", provider_name)


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
    selected_id = st.selectbox(
        "Abrir análise",
        list(labels),
        format_func=lambda value: labels[value],
    )
    if selected_id is None:
        return
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
    if st.button("Atualizar status") and new_status is not None:
        TRACKER.change_status(selected.id, new_status)
        st.success("Status atualizado.")
        st.rerun()


def render_dashboard_step() -> None:
    """Render local dashboard metrics."""
    _section_heading("DASHBOARD", "Visão geral da busca", "Acompanhamento das análises salvas.")
    records = TRACKER.list_analyses()
    with st.expander("Filtrar análises"):
        filters = st.columns(4)
        recommendation = filters[0].selectbox(
            "Recomendação",
            ["", "apply", "apply_with_adjustments", "save_for_later", "ignore"],
            format_func=lambda value: value.replace("_", " ").title() if value else "Todas",
        )
        modality = filters[1].selectbox(
            "Modalidade",
            ["", *MODALITIES],
            format_func=lambda value: modality_label(value) if value else "Todas",
        )
        seniority = filters[2].selectbox(
            "Senioridade",
            ["", *LEVELS],
            format_func=lambda value: seniority_label(value) if value else "Todas",
        )
        risk = filters[3].selectbox(
            "Risco",
            ["", "low", "medium", "high"],
            format_func=risk_label,
        )
        use_dates = st.checkbox("Filtrar por período")
        date_from = date_to = None
        if use_dates:
            dates = st.columns(2)
            date_from = dates[0].date_input("De")
            date_to = dates[1].date_input("Até")
    filtered = filter_dashboard_records(
        records,
        recommendation=recommendation,
        modality=modality,
        seniority=seniority,
        risk=risk,
        date_from=date_from,
        date_to=date_to,
    )
    metrics = calculate_dashboard_metrics(filtered)
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
                "Recomendação": item.analysis.recommendation,
                "Modalidade": modality_label(item.modality),
                "Senioridade": seniority_label(item.seniority),
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


def render_search_intelligence_step() -> None:
    """Render a manual-first search strategy without network automation."""
    _section_heading(
        "SEARCH INTELLIGENCE",
        "Plano seguro de busca",
        "Gera estratégia e termos de busca. Esta etapa não faz scraping automático.",
    )
    profile = st.session_state.resume_profile
    job = st.session_state.job_posting
    controls = st.columns(2)
    target_role = controls[0].text_input(
        "Cargo alvo",
        value=job.title or "Engenheiro de Software Júnior",
        key="search_target_role",
    )
    target_companies_text = controls[1].text_input(
        "Empresas ou domínios alvo",
        placeholder="empresa.com.br, startup alvo",
        key="search_target_companies",
    )
    strategy = SearchStrategyInput(
        target_role=target_role,
        skills=profile.skills[:8],
        location=job.location or profile.city,
        modality="" if job.modality == "unknown" else job.modality,
        seniority=job.seniority,
        target_companies=csv_items(target_companies_text),
        contract=job.contract,
    )
    plan = build_search_intelligence_plan(strategy)

    st.info("Nenhuma busca de rede foi executada. Copie as queries e pesquise manualmente.")
    sections = st.tabs(
        ["Queries sugeridas", "Cargos equivalentes", "Fontes", "Plano semanal", "Radar oculto"]
    )
    with sections[0]:
        for query in plan.queries:
            st.code(query)
    with sections[1]:
        render_list(plan.radar.alternative_roles, "Nenhum cargo alternativo sugerido.")
    with sections[2]:
        for source in plan.sources:
            st.markdown(f"**[{source.name}]({source.url})** · {source.reason}")
    with sections[3]:
        render_list(plan.weekly_plan, "Nenhum plano gerado.")
    with sections[4]:
        st.markdown("**Empresas onde faz sentido procurar**")
        render_list(plan.radar.target_company_ideas, "")
        st.markdown("**Alertas manuais sugeridos**")
        render_list(plan.radar.manual_alerts, "")
        st.markdown("**Riscos de vaga genérica**")
        render_list(plan.radar.generic_job_risks, "")


def render_app() -> None:
    """Configure and render the complete guided application."""
    st.set_page_config(page_title="SotuHire v0.5.0", page_icon="S", layout="wide")
    initialize_state()
    inject_styles()
    render_header()
    mode, provider_name = render_sidebar()
    if mode == "Modo rápido":
        render_quick_mode(provider_name)
        st.caption(
            "Processamento local por padrão · revisão humana obrigatória · sem auto-apply · "
            "sem invenção de experiência."
        )
        return

    st.markdown(
        '<div class="mode-banner"><strong>Modo avançado</strong>'
        "<span>Revisão completa, preferências, exports, histórico e estratégia de busca.</span></div>",
        unsafe_allow_html=True,
    )
    tabs = st.tabs(
        [
            "Currículo",
            "Vaga",
            "Preferências",
            "Resultado",
            "Search Intelligence",
            "Histórico",
            "Dashboard",
        ]
    )
    with tabs[0]:
        render_resume_step(advanced=True)
    with tabs[1]:
        render_job_step(advanced=True)
    with tabs[2]:
        render_preferences_step(mode)
    with tabs[3]:
        render_results_step("Modo avançado", provider_name)
    with tabs[4]:
        render_search_intelligence_step()
    with tabs[5]:
        render_history_step()
    with tabs[6]:
        render_dashboard_step()
    st.caption(
        "Processamento local por padrão · revisão humana obrigatória · sem auto-apply · "
        "sem invenção de experiência."
    )
