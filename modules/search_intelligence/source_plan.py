"""Build a safe manual-first source and weekly search plan."""

from __future__ import annotations

from modules.search_intelligence.schemas import (
    SearchIntelligencePlan,
    SearchStrategyInput,
    SourceSuggestion,
)


def build_source_suggestions(strategy: SearchStrategyInput) -> list[SourceSuggestion]:
    """Suggest public/manual sources appropriate for the target intent."""
    sources = [
        SourceSuggestion(
            name="LinkedIn Posts",
            url="https://www.linkedin.com/search/results/content/",
            reason="Encontrar posts públicos com vagas, indicações e times crescendo.",
            source_type="generic_public_page",
        ),
        SourceSuggestion(
            name="Gupy",
            url="https://portal.gupy.io/",
            reason="Buscar vagas corporativas brasileiras por cargo e senioridade.",
            source_type="generic_public_page",
        ),
        SourceSuggestion(
            name="Google Jobs",
            url="https://www.google.com/search?q=jobs",
            reason="Executar manualmente as queries sugeridas e comparar fontes.",
            source_type="generic_public_page",
        ),
        SourceSuggestion(
            name="Greenhouse",
            url="https://www.greenhouse.com/",
            reason="Pesquisar páginas públicas de carreira de empresas de tecnologia.",
            source_type="company_career_page",
        ),
    ]
    if strategy.seniority in {"estagio", "internship", "trainee"}:
        sources.append(
            SourceSuggestion(
                name="CIEE",
                url="https://portal.ciee.org.br/",
                reason="Priorizar estágio e início de carreira.",
                source_type="generic_public_page",
            )
        )
    if strategy.modality == "remote":
        sources.append(
            SourceSuggestion(
                name="Remotar",
                url="https://remotar.com.br/",
                reason="Priorizar oportunidades remotas no Brasil.",
                source_type="generic_public_page",
            )
        )
    return sources


def build_weekly_plan(strategy: SearchStrategyInput) -> list[str]:
    """Create a small repeatable routine rather than automatic scraping."""
    role = strategy.target_role or "cargo alvo"
    return [
        f"Segunda: executar as queries principais para {role} e salvar até 5 oportunidades.",
        "Quarta: procurar posts públicos, páginas de carreira e cargos equivalentes.",
        "Sexta: revisar respostas, atualizar histórico e ajustar termos que deram pouco resultado.",
        "Semanalmente: criar alertas manuais nas fontes preferidas e revisar vagas genéricas.",
    ]


def build_search_intelligence_plan(strategy: SearchStrategyInput) -> SearchIntelligencePlan:
    """Build the complete safe plan without network access."""
    from modules.search_intelligence.hidden_jobs_radar import build_hidden_jobs_radar
    from modules.search_intelligence.query_builder import build_search_queries

    return SearchIntelligencePlan(
        queries=build_search_queries(strategy),
        sources=build_source_suggestions(strategy),
        weekly_plan=build_weekly_plan(strategy),
        radar=build_hidden_jobs_radar(strategy),
        scraping_performed=False,
    )
