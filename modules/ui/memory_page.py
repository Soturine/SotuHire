"""Advanced-mode career memory management UI."""

from __future__ import annotations

from collections import Counter

import streamlit as st

from modules.memory import CareerMemory, CareerMemoryQuery
from modules.memory.memory_summarizer import memory_markdown_summary
from modules.profile import CareerProfileStore, build_career_profile, infer_preferences
from modules.ui.components import render_chips, render_item_cards, render_list
from modules.ui.layout import build_preferences

MEMORY = CareerMemory()
PROFILE_STORE = CareerProfileStore()


def _apply_inferred_preferences() -> None:
    inferred = infer_preferences(MEMORY.store.list_memory_items())
    st.session_state.preferred_modalities = inferred.modalities
    st.session_state.preferred_locations = ", ".join(inferred.locations)
    st.session_state.accepted_contracts = inferred.contracts
    st.session_state.target_levels = inferred.seniorities
    if inferred.target_roles:
        st.session_state.search_target_role = inferred.target_roles[0]
    if inferred.target_companies:
        st.session_state.search_target_companies = ", ".join(inferred.target_companies)


def _clear_inferred_preferences() -> None:
    st.session_state.preferred_modalities = []
    st.session_state.preferred_locations = ""
    st.session_state.accepted_contracts = []
    st.session_state.target_levels = []


def render_memory_page() -> None:
    """Render local memory overview, search, profile, and controls."""
    st.markdown("### Memória de carreira")
    st.info(
        "A memória de carreira é local por padrão. Você pode buscar, exportar, importar, "
        "desativar ou apagar quando quiser."
    )
    items = MEMORY.store.list_memory_items()
    profile = build_career_profile(
        st.session_state.resume_profile,
        items,
        build_preferences(),
    )
    PROFILE_STORE.save(profile)
    kinds = Counter(item.kind for item in items)
    tags = Counter(tag for item in items for tag in item.tags)
    metrics = st.columns(4)
    metrics[0].metric("Memórias", len(items))
    metrics[1].metric("Skills recorrentes", len(tags))
    metrics[2].metric("Gaps recorrentes", len(profile.recurring_gaps))
    metrics[3].metric("Cargos analisados", len(profile.target_roles))

    tabs = st.tabs(
        [
            "Visão geral",
            "Itens salvos",
            "Buscar",
            "Perfil profissional",
            "Preferências inferidas",
            "Privacidade e dados",
        ]
    )
    with tabs[0]:
        st.markdown("**Tipos de memória**")
        if kinds:
            st.dataframe(
                [{"Tipo": kind, "Quantidade": count} for kind, count in kinds.most_common()],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhuma memória local encontrada ainda.")
        st.markdown("**Skills e sinais recorrentes**")
        render_chips([tag for tag, _ in tags.most_common(20)], "Nenhum sinal recorrente.")
        st.markdown("**Últimas memórias**")
        render_item_cards(
            [f"{item.title}\n{item.source} · {item.kind}" for item in items[:8]],
            "Nenhuma memória salva.",
            visible_limit=8,
        )
    with tabs[1]:
        kind = st.selectbox("Filtrar por tipo", ["", *sorted(kinds)], key="memory_kind_filter")
        filtered = MEMORY.store.list_memory_items(kind=kind)
        for item in filtered[:100]:
            with st.container(border=True):
                st.markdown(f"**{item.title}** · `{item.kind}`")
                st.write(item.content)
                st.caption(f"Fonte: {item.source} · atualizado em {item.updated_at:%d/%m/%Y %H:%M}")
                if st.button("Excluir item", key=f"delete_memory_{item.id}"):
                    MEMORY.store.delete_memory_item(item.id)
                    st.rerun()
    with tabs[2]:
        query = st.text_input("Buscar na memória", key="memory_search_query")
        top_k = st.slider("Quantidade de resultados", 1, 20, 5, key="memory_search_top_k")
        if query.strip():
            evidence = MEMORY.retriever.retrieve(CareerMemoryQuery(query=query, top_k=top_k))
            for item in evidence:
                with st.container(border=True):
                    st.markdown(f"**{item.title}** · {item.source}")
                    st.write(item.excerpt)
                    st.caption(f"Relevância local: {item.relevance_score:.0%}")
    with tabs[3]:
        st.markdown("**Cargos alvo**")
        render_chips(profile.target_roles, "Ainda não inferidos.")
        st.markdown("**Skills técnicas**")
        render_chips(profile.technical_skills, "Nenhuma skill consolidada.")
        st.markdown("**Pontos fortes**")
        render_list(profile.strengths, "Ainda não há pontos fortes recorrentes.")
        st.markdown("**Lacunas recorrentes**")
        render_list(profile.recurring_gaps, "Ainda não há lacunas recorrentes.")
        st.markdown("**Projetos em destaque**")
        render_item_cards(profile.project_highlights, "Nenhum projeto consolidado.")
    with tabs[4]:
        inferred = infer_preferences(items)
        st.markdown("**Cargos e empresas**")
        render_chips([*inferred.target_roles, *inferred.target_companies], "Ainda não inferidos.")
        st.markdown("**Modalidades, contratos e senioridades**")
        render_chips(
            [*inferred.modalities, *inferred.contracts, *inferred.seniorities],
            "Ainda não inferidos.",
        )
        actions = st.columns(3)
        if actions[0].button("Aplicar preferências inferidas", use_container_width=True):
            _apply_inferred_preferences()
            st.success("Preferências inferidas aplicadas aos controles.")
        if actions[1].button("Editar manualmente", use_container_width=True):
            st.info("Use a aba Preferências para ajustar os valores aplicados.")
        if actions[2].button("Limpar inferências", use_container_width=True):
            _clear_inferred_preferences()
            st.success("Preferências inferidas removidas dos controles.")
    with tabs[5]:
        st.caption(
            "O uso local é padrão. O envio de contexto relevante ao Gemini exige confirmação."
        )
        export_actions = st.columns(2)
        if export_actions[0].button("Exportar memória", use_container_width=True):
            paths = MEMORY.export_all()
            st.success("Memória exportada: " + ", ".join(str(path) for path in paths.values()))
        export_actions[1].download_button(
            "Baixar resumo Markdown",
            memory_markdown_summary(items),
            "sotuhire-career-memory-summary.md",
            "text/markdown",
            use_container_width=True,
        )
        uploaded = st.file_uploader("Importar memória JSON ou JSONL", type=["json", "jsonl"])
        if uploaded and st.button("Importar memória"):
            imported = MEMORY.store.import_text(
                uploaded.getvalue().decode("utf-8"),
                suffix=f".{uploaded.name.rsplit('.', 1)[-1]}",
            )
            st.success(f"{imported} memórias importadas.")
            st.rerun()
        confirm_clear = st.checkbox("Confirmo que desejo apagar toda a memória local.")
        if st.button("Apagar memória local", disabled=not confirm_clear):
            MEMORY.store.clear()
            PROFILE_STORE.clear()
            st.success("Memória local apagada.")
            st.rerun()
