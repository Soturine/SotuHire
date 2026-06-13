"""Strategic hidden-jobs radar that never scrapes or contacts anyone."""

from __future__ import annotations

from modules.core.text_utils import normalize_text
from modules.search_intelligence.schemas import (
    HiddenJobsRadarPlan,
    SearchStrategyInput,
    SourceSuggestion,
)

ROLE_ALTERNATIVES = {
    "software": [
        "Desenvolvedor Backend Júnior",
        "Analista de Sistemas Júnior",
        "Engenheiro de Software Júnior",
        "Estágio em Desenvolvimento de Software",
    ],
    "dados": [
        "Analista de Dados Júnior",
        "Assistente de BI",
        "Estágio em Dados",
        "Analista de Relatórios Júnior",
    ],
    "frontend": [
        "Desenvolvedor Frontend Júnior",
        "Desenvolvedor Web Júnior",
        "Estágio em Frontend",
        "Pessoa Desenvolvedora React Júnior",
    ],
    "iot": [
        "Desenvolvedor IoT Júnior",
        "Estágio em Software Embarcado",
        "Técnico de Automação",
        "Analista de Sistemas Embarcados Júnior",
    ],
    "suporte": [
        "Técnico de Suporte Júnior",
        "Analista de Service Desk",
        "Analista de Suporte N1",
        "Assistente de TI",
    ],
}


def _alternative_roles(target_role: str) -> list[str]:
    normalized = normalize_text(target_role)
    for signal, roles in ROLE_ALTERNATIVES.items():
        if signal in normalized:
            return roles
    return [
        target_role,
        f"Assistente de {target_role}",
        f"Estágio em {target_role}",
        f"Analista Júnior - {target_role}",
    ]


def build_hidden_jobs_radar(strategy: SearchStrategyInput) -> HiddenJobsRadarPlan:
    """Return strategic suggestions based only on user-provided inputs."""
    skills = ", ".join(strategy.skills[:3]) or "skills principais"
    companies = strategy.target_companies or [
        "empresas locais do setor",
        "fornecedores de empresas-alvo",
        "startups e consultorias especializadas",
    ]
    actionable_sources = [
        SourceSuggestion(
            name=company,
            url=(
                company
                if company.startswith(("http://", "https://"))
                else f"https://{company}/careers"
            ),
            reason="Página pública de carreira indicada pelo radar.",
            source_type="company_career_page",
        )
        for company in strategy.target_companies
        if company.startswith(("http://", "https://")) or "." in company
    ]
    return HiddenJobsRadarPlan(
        alternative_roles=_alternative_roles(strategy.target_role),
        target_company_ideas=companies,
        manual_alerts=[
            f'Criar alerta manual para "{strategy.target_role}" e {skills}.',
            'Acompanhar posts com "estamos contratando", "vaga aberta" e "time crescendo".',
            "Revisar páginas públicas de carreira das empresas-alvo uma vez por semana.",
        ],
        generic_job_risks=[
            "Cargo sem senioridade ou responsabilidades claras.",
            "Post sem empresa, localização ou forma oficial de candidatura.",
            "Descrição genérica que pede muitas áreas sem prioridade.",
        ],
        actionable_sources=actionable_sources,
        scraping_performed=False,
    )
