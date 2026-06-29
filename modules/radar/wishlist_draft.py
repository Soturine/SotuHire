"""Local wishlist drafting for Job Radar free-text requests."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from modules.ai.schemas.analysis_insights import WishlistDraftOutput, WishlistDraftPayload
from modules.core.text_utils import normalize_text
from modules.profile.context import ProfileContext

AnalysisMode = Literal["ai", "local", "fallback"]

_DOMAIN_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "Saude",
        (
            "saude",
            "hospital",
            "clinica",
            "enfermagem",
            "enfermeiro",
            "coren",
            "uti",
            "medicina",
            "medico",
            "crm",
            "psicologia",
            "psicologo",
            "crp",
        ),
        ("Enfermeiro", "Tecnico de Enfermagem", "Assistente de Saude"),
        ("atendimento", "prontuario", "triagem", "plantao"),
    ),
    (
        "Direito",
        ("direito", "juridico", "advogado", "advocacia", "oab", "peticao", "audiencia"),
        ("Advogado Junior", "Assistente Juridico", "Estagio em Direito"),
        ("peticoes", "audiencias", "contratos", "pesquisa juridica"),
    ),
    (
        "Engenharia",
        (
            "engenharia",
            "engenharia civil",
            "civil",
            "crea",
            "cft",
            "tecnico industrial",
            "obra",
            "projeto tecnico",
            "processos",
            "qualidade",
            "nr10",
            "nr 10",
            "nr35",
            "nr 35",
        ),
        ("Estagio em Engenharia", "Analista de Engenharia", "Assistente Tecnico"),
        ("relatorios tecnicos", "Excel", "processos", "qualidade", "seguranca"),
    ),
    (
        "Educacao",
        ("educacao", "professor", "docente", "licenciatura", "aula", "pedagogia", "escola"),
        ("Professor", "Docente", "Assistente Pedagogico"),
        ("planejamento de aulas", "didatica", "avaliacao", "comunicacao"),
    ),
    (
        "Artes e Design",
        ("arte", "artes", "design", "portfolio", "ilustracao", "producao cultural"),
        ("Designer", "Assistente de Producao Cultural", "Ilustrador"),
        ("portfolio", "identidade visual", "ilustracao", "edicao", "criatividade"),
    ),
    (
        "Pesquisa e Laboratorio",
        (
            "pesquisa",
            "lattes",
            "laboratorio",
            "iniciacao cientifica",
            "congresso",
            "artigo",
            "quimica",
            "crq",
        ),
        ("Assistente de Pesquisa", "Tecnico de Laboratorio", "Bolsista de Pesquisa"),
        ("metodologia", "analise de dados", "relatorio", "laboratorio"),
    ),
    (
        "Tecnologia e Dados",
        ("python", "sql", "dados", "api", "software", "backend", "frontend", "power bi"),
        ("Analista de Dados", "Desenvolvedor", "Analista de Sistemas"),
        ("Python", "SQL", "Excel", "Power BI", "APIs"),
    ),
    (
        "Administracao e Operacoes",
        ("administracao", "operacoes", "financeiro", "atendimento", "compras", "estoque"),
        ("Assistente Administrativo", "Analista de Operacoes", "Assistente Financeiro"),
        ("Excel", "atendimento", "organizacao", "relatorios", "processos"),
    ),
    (
        "Turismo e Servicos",
        ("turismo", "hotelaria", "guia", "guia de turismo", "idiomas", "evento", "recepcao"),
        ("Assistente de Turismo", "Recepcionista", "Guia de Turismo"),
        ("idiomas", "atendimento", "organizacao", "eventos", "comunicacao"),
    ),
)

_SENIORITY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("estagio", ("estagio", "estudante", "graduando", "aprendiz")),
    ("junior", ("junior", "primeira vaga", "inicio de carreira", "recem formado")),
    ("pleno", ("pleno", "experiencia intermediaria", "autonomia")),
    ("senior", ("senior", "lideranca", "especialista", "mais de 5 anos")),
)


def build_local_wishlist_draft(
    free_text: str,
    *,
    profile_context: ProfileContext | None = None,
    provider_used: str = "local",
    analysis_mode: AnalysisMode = "local",
    warnings: Iterable[str] = (),
) -> WishlistDraftOutput:
    """Build an unsaved wishlist draft from text and optional local context."""
    normalized = normalize_text(free_text)
    detected_domains = _detect_domains(normalized)
    seniorities = _detect_seniority(normalized)
    titles = _titles_for_domains(detected_domains)
    skills = _merge(
        _skills_for_domains(detected_domains), _explicit_requirements_from_text(normalized)
    )
    desired_skills = _desired_from_text(normalized)
    locations = _detect_locations(free_text, normalized)
    remote_preferences = _detect_remote_preferences(normalized)
    excluded_terms = _detect_excluded_terms(free_text, normalized)
    contract_types = _detect_contracts(normalized)

    if profile_context is not None:
        titles = _merge(titles, profile_context.career_goals)
        skills = _merge(skills, [item.title for item in profile_context.skills[:12]])
        locations = _merge(locations, profile_context.locations)
        desired_skills = _merge(desired_skills, profile_context.preferences[:10])
        if not seniorities:
            seniorities = _extract_seniority_from_context(profile_context)

    name_base = detected_domains[0] if detected_domains else "Busca"
    wishlist = WishlistDraftPayload(
        name=f"Wishlist sugerida - {name_base}",
        target_titles=titles[:8],
        target_domains=detected_domains[:6],
        target_seniority=seniorities[:5],
        required_skills=skills[:12],
        desired_skills=desired_skills[:12],
        excluded_terms=excluded_terms[:8],
        locations=locations[:8],
        remote_preferences=remote_preferences[:5],
        work_model=remote_preferences[0] if remote_preferences else "",
        employment_type=contract_types[0] if contract_types else "",
        contract_types=contract_types[:6],
        industries=detected_domains[:6],
        source_types=["public_feed", "manual_url", "manual_public_page"],
        min_match_score=70,
        min_ats_score=60,
        notify_on_new_matches=True,
        is_active=True,
        notes=(
            "Rascunho gerado a partir de texto livre. Revise cargos, requisitos e filtros "
            "antes de salvar."
        ),
    )

    assumptions = [
        "Usei apenas sinais do texto livre e do contexto local permitido.",
        "Campos ausentes ficaram em branco ou como sugestoes conservadoras.",
    ]
    questions = [
        "Quais cargos voce realmente aceita?",
        "Alguma cidade, contrato, escala ou empresa deve ser excluida?",
        "Quais habilidades sao obrigatorias e quais sao apenas desejaveis?",
    ]
    if profile_context is None:
        questions.append("Deseja usar o perfil local para complementar preferencias?")

    final_warnings = [
        *warnings,
        "A wishlist nao foi salva automaticamente; revise antes de confirmar.",
        "Nao inventei formacao, registro profissional, certificacao ou experiencia.",
    ]
    return WishlistDraftOutput(
        wishlist=wishlist,
        confidence=_confidence(detected_domains, skills, titles),
        detected_domains=detected_domains,
        detected_career_moments=seniorities,
        assumptions=assumptions,
        questions_to_confirm=questions,
        warnings=_merge([], final_warnings),
        needs_user_review=True,
        provider_used=provider_used,
        analysis_mode=analysis_mode,
    )


def _detect_domains(normalized: str) -> list[str]:
    domains: list[str] = []
    for domain, keywords, _, _ in _DOMAIN_RULES:
        if any(keyword in normalized for keyword in keywords):
            domains.append(domain)
    return domains or ["Geral"]


def _titles_for_domains(domains: list[str]) -> list[str]:
    titles: list[str] = []
    for domain, _, domain_titles, _ in _DOMAIN_RULES:
        if domain in domains:
            titles = _merge(titles, domain_titles)
    return titles or ["Assistente", "Analista Junior", "Estagio"]


def _skills_for_domains(domains: list[str]) -> list[str]:
    skills: list[str] = []
    for domain, _, _, domain_skills in _DOMAIN_RULES:
        if domain in domains:
            skills = _merge(skills, domain_skills)
    return skills or ["comunicacao", "organizacao", "aprendizado continuo"]


def _detect_seniority(normalized: str) -> list[str]:
    return [label for label, keywords in _SENIORITY_RULES if any(k in normalized for k in keywords)]


def _detect_locations(original: str, normalized: str) -> list[str]:
    locations: list[str] = []
    known = {
        "brasil": "Brasil",
        "sao paulo": "Sao Paulo",
        "sao jose dos campos": "Sao Jose dos Campos",
        "jacarei": "Jacarei",
        "rio de janeiro": "Rio de Janeiro",
        "belo horizonte": "Belo Horizonte",
        "curitiba": "Curitiba",
        "porto alegre": "Porto Alegre",
        "recife": "Recife",
        "salvador": "Salvador",
    }
    for needle, label in known.items():
        if needle in normalized:
            locations.append(label)
    if "remoto" in normalized:
        locations.append("Remoto")
    if "hibrido" in normalized or "hybrid" in normalized:
        locations.append("Hibrido")
    if not locations and original.strip():
        locations.append("Brasil")
    return _merge([], locations)


def _detect_remote_preferences(normalized: str) -> list[str]:
    preferences: list[str] = []
    if "remoto" in normalized:
        preferences.append("remoto")
    if "hibrido" in normalized or "hybrid" in normalized:
        preferences.append("hibrido")
    if "presencial" in normalized:
        preferences.append("presencial")
    return preferences


def _detect_contracts(normalized: str) -> list[str]:
    contracts: list[str] = []
    for term, label in {
        "clt": "CLT",
        "pj": "PJ",
        "estagio": "estagio",
        "trainee": "trainee",
        "temporario": "temporario",
        "bolsa": "bolsa",
    }.items():
        if term in normalized:
            contracts.append(label)
    return contracts


def _detect_excluded_terms(original: str, normalized: str) -> list[str]:
    excluded: list[str] = []
    markers = {
        "nao quero pj": "PJ",
        "sem pj": "PJ",
        "nao quero presencial": "presencial integral",
        "sem presencial": "presencial integral",
        "sem remuneracao": "sem remuneracao",
        "nao remunerado": "nao remunerado",
    }
    for needle, label in markers.items():
        if needle in normalized:
            excluded.append(label)
    if "excluir:" in normalize_text(original):
        excluded.append("termos marcados pelo usuario em excluir")
    return excluded


def _desired_from_text(normalized: str) -> list[str]:
    desired: list[str] = []
    for needle, label in {
        "excel": "Excel",
        "power bi": "Power BI",
        "python": "Python",
        "sql": "SQL",
        "ingles": "ingles",
        "espanhol": "espanhol",
        "lattes": "Lattes",
        "portfolio": "portfolio",
        "cnh": "CNH",
    }.items():
        if needle in normalized:
            desired.append(label)
    return desired


def _explicit_requirements_from_text(normalized: str) -> list[str]:
    requirements: list[str] = []
    for needle, label in {
        "coren": "COREN",
        "oab": "OAB",
        "crm": "CRM",
        "crp": "CRP",
        "crea": "CREA",
        "cft": "CFT",
        "crq": "CRQ",
        "crc": "CRC",
        "cau": "CAU",
        "crf": "CRF",
        "nr10": "NR10",
        "nr 10": "NR10",
        "nr35": "NR35",
        "nr 35": "NR35",
        "lattes": "Lattes",
    }.items():
        if needle in normalized:
            requirements.append(label)
    return requirements


def _extract_seniority_from_context(profile_context: ProfileContext) -> list[str]:
    signals = normalize_text(" ".join(profile_context.application_history_signals))
    return _detect_seniority(signals)


def _confidence(domains: list[str], skills: list[str], titles: list[str]) -> float:
    score = 0.35
    if domains and domains != ["Geral"]:
        score += 0.2
    if skills:
        score += 0.2
    if titles:
        score += 0.15
    return round(min(score, 0.88), 2)


def _merge(primary: Iterable[str], secondary: Iterable[str]) -> list[str]:
    merged: list[str] = []
    for item in [*primary, *secondary]:
        cleaned = str(item).strip()
        if cleaned and normalize_text(cleaned) not in {
            normalize_text(existing) for existing in merged
        }:
            merged.append(cleaned)
    return merged
