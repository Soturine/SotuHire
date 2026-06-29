"""Local fallback extraction for universal profile items."""

from __future__ import annotations

from collections.abc import Iterable

from modules.core.text_utils import normalize_text
from modules.profile.models import ProfileImportDraft, ProfileItem

_DOMAIN_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Saude", ("saude", "hospital", "clinica", "enfermagem", "coren", "crm", "crp", "uti")),
    ("Direito", ("direito", "juridico", "advogado", "oab", "peticao", "audiencia")),
    (
        "Engenharia",
        ("engenharia", "crea", "cft", "obra", "industrial", "nr10", "nr 10", "nr35", "nr 35"),
    ),
    ("Educacao", ("educacao", "professor", "licenciatura", "pedagogia", "escola", "aula")),
    ("Artes e Design", ("arte", "artes", "design", "portfolio", "ilustracao", "behance")),
    ("Pesquisa e Laboratorio", ("pesquisa", "lattes", "orcid", "laboratorio", "crq", "congresso")),
    ("Turismo e Servicos", ("turismo", "guia", "hotelaria", "idiomas", "recepcao")),
    ("Administracao e Operacoes", ("administracao", "financeiro", "compras", "atendimento")),
    ("Tecnologia e Dados", ("python", "sql", "software", "dados", "github", "api")),
)

_ITEM_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "education",
        ("ensino medio", "graduacao", "bacharel", "licenciatura", "faculdade"),
        "Formacao",
    ),
    ("technical_education", ("curso tecnico", "tecnico em", "tecnologo"), "Formacao tecnica"),
    ("postgraduate_education", ("pos-graduacao", "mba", "mestrado", "doutorado"), "Pos-graduacao"),
    ("language_course", ("ingles", "espanhol", "frances", "idioma"), "Idioma"),
    (
        "certification",
        ("certificacao", "certificado", "certificada", "certificado em"),
        "Certificacao",
    ),
    (
        "professional_registry",
        (
            "coren",
            "oab",
            "crm",
            "crp",
            "crea",
            "crq",
            "cft",
            "crc",
            "cau",
            "cref",
            "crf",
            "crmv",
            "cress",
            "crn",
            "cro",
        ),
        "Registro profissional",
    ),
    ("standard_or_norm", ("nr10", "nr 10", "nr35", "nr 35", "nr12", "nr 12"), "Norma ou NR"),
    ("research", ("iniciacao cientifica", "pesquisa", "lattes", "orcid"), "Pesquisa"),
    ("publication", ("publicacao", "artigo", "congresso", "anais"), "Publicacao"),
    ("portfolio", ("portfolio", "behance", "artstation", "instagram profissional"), "Portfolio"),
    ("project", ("projeto", "tcc", "extensao", "empresa junior"), "Projeto"),
    ("volunteer_work", ("voluntariado", "voluntario"), "Voluntariado"),
    ("freelance_work", ("freelancer", "autonomo"), "Trabalho autonomo"),
    ("internship", ("estagio", "estagiario"), "Estagio"),
    ("residency", ("residencia", "internato"), "Residencia ou internato"),
    ("clinical_practice", ("clinica-escola", "atendimento clinico", "plantao"), "Pratica clinica"),
    ("teaching_practice", ("sala de aula", "monitoria", "docencia"), "Pratica docente"),
    (
        "laboratory_practice",
        ("laboratorio", "bancada", "analise quimica"),
        "Pratica de laboratorio",
    ),
    ("field_work", ("obra", "campo", "levantamento"), "Trabalho de campo"),
    ("technical_skill", ("excel", "power bi", "python", "sql", "autocad"), "Competencia tecnica"),
    (
        "soft_skill",
        ("comunicacao", "lideranca", "organizacao", "atendimento"),
        "Competencia comportamental",
    ),
)


def extract_profile_items_local(
    text: str,
    *,
    source_type: str = "manual_notes",
    warnings: Iterable[str] = (),
) -> ProfileImportDraft:
    """Extract conservative profile item drafts from pasted text."""
    normalized = normalize_text(text)
    domains = _detect_domains(normalized)
    career_moments = _detect_career_moments(normalized)
    items = _items_from_text(text, normalized, source_type=source_type, domains=domains)
    return ProfileImportDraft(
        items=items,
        detected_domains=domains,
        career_moments=career_moments,
        warnings=[
            *warnings,
            "Extração local conservadora: revise antes de adicionar ao perfil.",
        ],
        questions_to_confirm=[
            "Quais itens devem entrar como fatos confirmados?",
            "Algum registro, curso ou certificação precisa de evidência adicional?",
        ],
        provider_used="local",
        requested_provider="local",
        analysis_mode="local",
        needs_user_review=True,
    )


def _items_from_text(
    original: str,
    normalized: str,
    *,
    source_type: str,
    domains: list[str],
) -> list[ProfileItem]:
    snippets = _sentences(original)
    items: list[ProfileItem] = []
    for item_type, keywords, fallback_title in _ITEM_RULES:
        if not any(keyword in normalized for keyword in keywords):
            continue
        evidence = _first_matching_sentence(snippets, keywords) or original[:300]
        title = _title_for_item(item_type, normalized, fallback_title)
        item = ProfileItem(
            type=item_type,
            title=title,
            description=evidence,
            area=domains[0] if domains else None,
            domain=domains[0] if domains else None,
            tags=_tags_for_text(normalized),
            skills=_skills_for_text(normalized),
            evidence=evidence,
            source=source_type,
            confidence="high" if _has_explicit_marker(item_type, normalized) else "medium",
            confirmed_by_user=False,
        )
        items.append(item)
    if not items and original.strip():
        items.append(
            ProfileItem(
                type="application_signal",
                title="Informação de perfil a revisar",
                description=original[:500],
                area=domains[0] if domains else None,
                domain=domains[0] if domains else None,
                evidence=original[:500],
                source=source_type,
                confidence="low",
                confirmed_by_user=False,
            )
        )
    return _dedupe_items(items)


def _detect_domains(normalized: str) -> list[str]:
    domains: list[str] = []
    for domain, keywords in _DOMAIN_RULES:
        if any(keyword in normalized for keyword in keywords):
            domains.append(domain)
    return domains or ["Geral"]


def _detect_career_moments(normalized: str) -> list[str]:
    moments: list[str] = []
    for needle, label in {
        "estagio": "estagio",
        "estudante": "estudante",
        "recem formado": "recem_formado",
        "junior": "junior",
        "trainee": "trainee",
        "transicao": "transicao_de_carreira",
        "mestrado": "pos_graduacao",
        "doutorado": "pos_graduacao",
    }.items():
        if needle in normalized:
            moments.append(label)
    return _unique(moments)


def _title_for_item(item_type: str, normalized: str, fallback: str) -> str:
    explicit = {
        "professional_registry": {
            "coren": "COREN",
            "oab": "OAB",
            "crm": "CRM",
            "crp": "CRP",
            "crea": "CREA",
            "crq": "CRQ",
            "cft": "CFT",
            "crc": "CRC",
            "cau": "CAU",
            "cref": "CREF",
            "crf": "CRF",
            "crmv": "CRMV",
            "cress": "CRESS",
            "crn": "CRN",
            "cro": "CRO",
        },
        "standard_or_norm": {
            "nr10": "NR10",
            "nr 10": "NR10",
            "nr35": "NR35",
            "nr 35": "NR35",
            "nr12": "NR12",
            "nr 12": "NR12",
        },
    }
    for needle, label in explicit.get(item_type, {}).items():
        if needle in normalized:
            return label
    if item_type == "language_course":
        languages = [
            label
            for needle, label in {
                "ingles": "Inglês",
                "espanhol": "Espanhol",
                "frances": "Francês",
            }.items()
            if needle in normalized
        ]
        if languages:
            return ", ".join(languages)
    return fallback


def _has_explicit_marker(item_type: str, normalized: str) -> bool:
    return item_type in {"professional_registry", "standard_or_norm"} and any(
        marker in normalized
        for marker in (
            "coren",
            "oab",
            "crm",
            "crp",
            "crea",
            "crq",
            "cft",
            "crc",
            "cau",
            "cref",
            "crf",
            "crmv",
            "cress",
            "crn",
            "cro",
            "nr10",
            "nr 10",
            "nr35",
            "nr 35",
        )
    )


def _tags_for_text(normalized: str) -> list[str]:
    tags = []
    for needle, label in {
        "lattes": "Lattes",
        "portfolio": "portfólio",
        "laboratorio": "laboratório",
        "atendimento": "atendimento",
        "obra": "obra",
        "hospital": "hospital",
        "escola": "escola",
        "turismo": "turismo",
    }.items():
        if needle in normalized:
            tags.append(label)
    return _unique(tags)


def _skills_for_text(normalized: str) -> list[str]:
    skills = []
    for needle, label in {
        "excel": "Excel",
        "power bi": "Power BI",
        "python": "Python",
        "sql": "SQL",
        "autocad": "AutoCAD",
        "atendimento": "atendimento",
        "relatorio": "relatórios",
        "ingles": "Inglês",
        "espanhol": "Espanhol",
    }.items():
        if needle in normalized:
            skills.append(label)
    return _unique(skills)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in text.replace("\n", ". ").split(".") if part.strip()]


def _first_matching_sentence(sentences: list[str], keywords: tuple[str, ...]) -> str:
    for sentence in sentences:
        normalized = normalize_text(sentence)
        if any(keyword in normalized for keyword in keywords):
            return sentence
    return ""


def _dedupe_items(items: list[ProfileItem]) -> list[ProfileItem]:
    seen: set[tuple[str, str]] = set()
    unique: list[ProfileItem] = []
    for item in items:
        key = (item.type, normalize_text(item.title))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _unique(values: Iterable[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and normalize_text(cleaned) not in {
            normalize_text(existing) for existing in unique
        }:
            unique.append(cleaned)
    return unique
