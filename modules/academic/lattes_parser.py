"""Conservative parser for pasted Curriculo Lattes or academic text."""

from __future__ import annotations

import re
from collections.abc import Iterable

from modules.academic.lattes_models import LattesImportInput, LattesImportResult
from modules.core.text_utils import normalize_text
from modules.profile.models import ProfileConfidence, ProfileItem

_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
_ORCID_RE = re.compile(r"\b\d{4}-\d{4}-\d{4}-[\dXx]{4}\b")
_LATTES_URL_RE = re.compile(r"lattes\.cnpq\.br/(\d+)", re.IGNORECASE)
_ISBN_RE = re.compile(r"\b(?:ISBN[:\s]*)?97[89][-\s]?\d[-\s]?\d{2,5}[-\s]?\d{2,7}[-\s]?\d\b")
_ISSN_RE = re.compile(r"\b(?:ISSN[:\s]*)?\d{4}-\d{3}[\dXx]\b")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_SECTION_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Identificação", ("identificacao", "dados pessoais")),
    (
        "Formação acadêmica/titulação",
        ("formacao academica titulacao", "formacao academica", "titulacao"),
    ),
    ("Formação complementar", ("formacao complementar", "cursos complementares")),
    ("Atuação profissional", ("atuacao profissional", "vinculos profissionais")),
    ("Projetos de pesquisa", ("projetos de pesquisa", "projeto de pesquisa")),
    ("Projetos de extensão", ("projetos de extensao", "projeto de extensao")),
    ("Projetos de desenvolvimento", ("projetos de desenvolvimento", "desenvolvimento")),
    ("Áreas de atuação", ("areas de atuacao", "area de atuacao")),
    ("Produções bibliográficas", ("producoes bibliograficas", "producao bibliografica")),
    (
        "Artigos completos publicados em periódicos",
        ("artigos completos publicados em periodicos", "artigos completos", "periodicos"),
    ),
    ("Trabalhos publicados em anais", ("trabalhos publicados em anais", "anais")),
    ("Livros e capítulos", ("livros e capitulos", "capitulos de livros", "livros publicados")),
    ("Produção técnica", ("producao tecnica", "produtos tecnologicos")),
    ("Produção artística/cultural", ("producao artistica", "producao cultural")),
    ("Bancas", ("bancas", "participacao em bancas")),
    ("Orientações", ("orientacoes", "orientacao", "supervisao")),
    ("Participação em eventos", ("participacao em eventos", "eventos")),
    ("Apresentações de trabalho", ("apresentacoes de trabalho", "apresentacao de trabalho")),
    ("Prêmios e títulos", ("premios e titulos", "premios")),
    ("Idiomas", ("idiomas", "linguas")),
    ("Linhas de pesquisa", ("linhas de pesquisa", "linha de pesquisa")),
    ("Bolsas", ("bolsas", "auxilios", "fomento")),
    ("Iniciação científica", ("iniciacao cientifica", "pibic", "pibiti")),
    ("Monitoria", ("monitoria", "monitor")),
    ("Docência", ("docencia", "ensino", "disciplinas ministradas")),
)

_SECTION_TYPES: dict[str, str] = {
    "Formação complementar": "short_course",
    "Atuação profissional": "professional_experience",
    "Projetos de pesquisa": "research_project",
    "Projetos de extensão": "extension_project",
    "Projetos de desenvolvimento": "technical_production",
    "Áreas de atuação": "research_area",
    "Produções bibliográficas": "publication",
    "Artigos completos publicados em periódicos": "journal_article",
    "Trabalhos publicados em anais": "conference_paper",
    "Livros e capítulos": "book_chapter",
    "Produção técnica": "technical_production",
    "Produção artística/cultural": "artistic_production",
    "Bancas": "exam_board",
    "Orientações": "academic_advising",
    "Participação em eventos": "event_participation",
    "Apresentações de trabalho": "presentation",
    "Prêmios e títulos": "award",
    "Idiomas": "language",
    "Linhas de pesquisa": "research_area",
    "Bolsas": "scholarship",
    "Iniciação científica": "scientific_initiation",
    "Monitoria": "monitoring",
    "Docência": "teaching_experience",
}

_ACADEMIC_TYPE_LABELS: dict[str, str] = {
    "academic_profile": "Perfil acadêmico",
    "curriculum_lattes": "Currículo Lattes informado",
    "lattes_identifier": "Identificador Lattes",
    "orcid": "ORCID",
    "research_area": "Área ou linha de pesquisa",
    "cnpq_area": "Área CNPq",
    "higher_education": "Formação superior",
    "technical_education": "Formação técnica",
    "postgraduate_education": "Pós-graduação",
    "specialization": "Especialização",
    "mba": "MBA",
    "master_degree": "Mestrado",
    "doctorate": "Doutorado",
    "postdoc": "Pós-doutorado",
    "scientific_initiation": "Iniciação científica",
    "research_project": "Projeto de pesquisa",
    "extension_project": "Projeto de extensão",
    "teaching_project": "Projeto de docência",
    "monitoring": "Monitoria",
    "teaching_experience": "Experiência docente",
    "teaching_assistant": "Assistência docente",
    "laboratory_practice": "Prática de laboratório",
    "field_work": "Trabalho de campo",
    "clinical_practice": "Prática clínica",
    "publication": "Publicação",
    "journal_article": "Artigo em periódico",
    "conference_paper": "Trabalho em anais",
    "book": "Livro",
    "book_chapter": "Capítulo de livro",
    "technical_report": "Relatório técnico",
    "patent": "Patente",
    "software_registration": "Registro de software",
    "dataset": "Dataset",
    "presentation": "Apresentação de trabalho",
    "event_participation": "Participação em evento",
    "course_taught": "Curso ministrado",
    "short_course": "Curso de curta duração",
    "lecture": "Palestra",
    "award": "Prêmio ou título",
    "grant": "Fomento",
    "scholarship": "Bolsa",
    "academic_advising": "Orientação acadêmica",
    "exam_board": "Banca",
    "reviewer_activity": "Atividade de revisão",
    "artistic_production": "Produção artística",
    "technical_production": "Produção técnica",
    "portfolio_academic": "Portfólio acadêmico",
}

_TYPE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("postdoc", ("pos doutorado", "pos-doutorado", "postdoc")),
    ("doctorate", ("doutorado", "doutoramento")),
    ("master_degree", ("mestrado", "mestre em")),
    ("mba", ("mba",)),
    ("specialization", ("especializacao", "especialista")),
    ("postgraduate_education", ("pos graduacao", "pos-graduacao")),
    ("higher_education", ("graduacao", "bacharelado", "licenciatura", "tecnologo")),
    ("technical_education", ("curso tecnico", "tecnico em")),
    ("journal_article", ("periodico", "revista", "journal", "doi")),
    ("conference_paper", ("anais", "congresso", "simposio", "seminario")),
    ("book_chapter", ("capitulo", "chapter")),
    ("book", ("livro", "book")),
    ("technical_report", ("relatorio tecnico",)),
    ("patent", ("patente",)),
    ("software_registration", ("registro de software", "software registrado")),
    ("dataset", ("dataset", "base de dados")),
    ("research_project", ("projeto de pesquisa", "pesquisa")),
    ("extension_project", ("projeto de extensao", "extensao")),
    ("teaching_experience", ("docencia", "disciplina", "professor", "aula")),
    ("teaching_assistant", ("assistente docente", "teaching assistant")),
    ("monitoring", ("monitoria", "monitor")),
    ("scientific_initiation", ("iniciacao cientifica", "pibic", "pibiti")),
    ("laboratory_practice", ("laboratorio", "bancada")),
    ("field_work", ("trabalho de campo", "campo")),
    ("clinical_practice", ("pratica clinica", "clinica")),
    ("grant", ("fapesp", "capes", "cnpq", "fapemig", "faperj", "fomento")),
    ("scholarship", ("bolsa", "bolsista", "pibic", "pibiti")),
    ("lecture", ("palestra", "conferencia")),
    ("course_taught", ("curso ministrado", "ministrou")),
    ("reviewer_activity", ("revisor", "parecerista", "reviewer")),
    ("portfolio_academic", ("tcc", "dissertacao", "tese", "portfolio academico")),
)

_DOMAIN_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Pesquisa acadêmica", ("pesquisa", "lattes", "cnpq", "capes", "fapesp")),
    ("Docência", ("docencia", "ensino", "disciplina", "monitoria")),
    ("Extensão universitária", ("extensao", "comunidade", "projeto social")),
    ("Produção científica", ("artigo", "periodico", "anais", "doi", "publicacao")),
    ("Produção técnica", ("software", "patente", "relatorio tecnico", "dataset")),
    ("Produção artística", ("artistica", "cultural", "exposicao", "performance")),
    ("Laboratório", ("laboratorio", "experimento", "bancada")),
)


def parse_lattes_text(payload: LattesImportInput) -> LattesImportResult:
    """Extract review-only academic ProfileItems from pasted text."""
    text = payload.text.strip()
    normalized = normalize_text(text)
    sections = _section_blocks(text)
    identifiers = _explicit_identifiers(text, payload)
    items: list[ProfileItem] = []

    if identifiers["lattes"]:
        items.append(
            _item(
                "lattes_identifier",
                f"Lattes {identifiers['lattes']}",
                _identifier_evidence(text, identifiers["lattes"])
                or "Identificador Lattes informado.",
                payload,
                source_ref=identifiers["lattes"],
                confidence="high",
                tags=["Lattes"],
            )
        )
    if identifiers["orcid"]:
        items.append(
            _item(
                "orcid",
                f"ORCID {identifiers['orcid']}",
                _identifier_evidence(text, identifiers["orcid"]) or "ORCID informado.",
                payload,
                source_ref=identifiers["orcid"],
                confidence="high",
                tags=["ORCID"],
            )
        )

    for section_name, lines in sections.items():
        items.extend(_items_from_section(section_name, lines, payload, normalized))

    if not items and text:
        items.append(
            _item(
                "academic_profile",
                "Texto acadêmico a revisar",
                _short_evidence(text),
                payload,
                confidence="low",
            )
        )

    deduped = _dedupe_items(items)
    detected_sections = [name for name in sections if name != "Texto acadêmico"] or [
        "Texto acadêmico"
    ]
    warnings = [
        "Extração local conservadora: nada é salvo sem revisão humana.",
        "O SotuHire não acessa sua conta Lattes nem faz scraping autenticado.",
    ]
    assumptions: list[str] = []
    if "Texto acadêmico" in sections and len(sections) == 1:
        assumptions.append("Estrutura de seções não foi detectada; usei heurísticas locais.")
    if any(item.confidence == "low" for item in deduped):
        warnings.append("Itens de baixa confiança precisam de confirmação explícita.")

    return LattesImportResult(
        items=deduped,
        detected_sections=detected_sections,
        assumptions=assumptions,
        questions_to_confirm=[
            "Quais itens extraídos representam fatos que você quer manter no Perfil?",
            "Alguma publicação, DOI, vínculo, instituição ou bolsa precisa ser corrigida?",
            "Algum item sensível deve permanecer fora do Perfil?",
        ],
        warnings=warnings,
        confidence=_overall_confidence(deduped, detected_sections),
        needs_user_review=True,
        provider_used="local",
        requested_provider="local",
        analysis_mode="local",
    )


def _section_blocks(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "Texto acadêmico"
    for raw_line in text.splitlines():
        line = raw_line.strip(" \t:-")
        if not line:
            continue
        section = _section_name(line)
        if section is not None:
            current = section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    if not sections:
        sections["Texto acadêmico"] = [text]
    return sections


def _section_name(line: str) -> str | None:
    normalized = normalize_text(line).replace("/", " ")
    compact = normalized.rstrip(":")
    if len(compact) > 90:
        return None
    for canonical, aliases in _SECTION_ALIASES:
        if any(compact == alias or compact.startswith(alias + " ") for alias in aliases):
            return canonical
    return None


def _items_from_section(
    section_name: str,
    lines: list[str],
    payload: LattesImportInput,
    full_normalized_text: str,
) -> list[ProfileItem]:
    if not lines:
        return []
    if section_name == "Identificação":
        return _identity_items(lines, payload)
    if section_name == "Formação acadêmica/titulação":
        return [
            _line_item(_education_type(line), line, payload, confidence="high")
            for line in _relevant_lines(lines)
        ]
    fallback_type = _SECTION_TYPES.get(section_name, "academic_profile")
    items: list[ProfileItem] = []
    for line in _relevant_lines(lines):
        item_type = _infer_item_type(line, fallback_type, section_name)
        confidence: ProfileConfidence = "high" if _has_strong_marker(line, item_type) else "medium"
        if item_type == "research_area" and "cnpq" in normalize_text(line):
            item_type = "cnpq_area"
        items.append(_line_item(item_type, line, payload, confidence=confidence))
    if not items and section_name == "Texto acadêmico":
        items.extend(_items_from_unsectioned_text(lines, payload, full_normalized_text))
    return items


def _identity_items(lines: list[str], payload: LattesImportInput) -> list[ProfileItem]:
    joined = "\n".join(lines)
    normalized = normalize_text(joined)
    items: list[ProfileItem] = []
    if "lattes" in normalized:
        items.append(
            _item(
                "curriculum_lattes",
                "Currículo Lattes informado",
                _short_evidence(joined),
                payload,
                confidence="medium",
                tags=["Lattes"],
            )
        )
    if "orcid" in normalized and not payload.orcid:
        for orcid in _ORCID_RE.findall(joined):
            items.append(
                _item(
                    "orcid",
                    f"ORCID {orcid.upper()}",
                    _identifier_evidence(joined, orcid),
                    payload,
                    source_ref=orcid.upper(),
                    confidence="high",
                    tags=["ORCID"],
                )
            )
    return items


def _items_from_unsectioned_text(
    lines: list[str],
    payload: LattesImportInput,
    full_normalized_text: str,
) -> list[ProfileItem]:
    items: list[ProfileItem] = []
    for line in _relevant_lines(lines, max_lines=12):
        normalized = normalize_text(line)
        item_type = _infer_item_type(line, "academic_profile", "Texto acadêmico")
        if item_type == "academic_profile" and not any(
            keyword in normalized
            for _, keywords in [
                *_TYPE_KEYWORDS,
                *[(name, aliases) for name, aliases in _SECTION_ALIASES],
            ]
            for keyword in keywords
        ):
            continue
        items.append(
            _line_item(
                item_type,
                line,
                payload,
                confidence="high" if _has_strong_marker(line, item_type) else "medium",
            )
        )
    if not items and any(marker in full_normalized_text for marker in ("lattes", "orcid", "doi")):
        items.append(
            _item(
                "academic_profile",
                "Evidência acadêmica a revisar",
                _short_evidence("\n".join(lines)),
                payload,
                confidence="low",
            )
        )
    return items


def _education_type(line: str) -> str:
    normalized = normalize_text(line)
    for item_type, keywords in _TYPE_KEYWORDS:
        if item_type in {
            "postdoc",
            "doctorate",
            "master_degree",
            "mba",
            "specialization",
            "postgraduate_education",
            "higher_education",
            "technical_education",
        } and any(keyword in normalized for keyword in keywords):
            return item_type
    return "higher_education"


def _infer_item_type(line: str, fallback_type: str, section_name: str) -> str:
    normalized = normalize_text(line)
    if section_name == "Livros e capítulos":
        if "capitulo" in normalized:
            return "book_chapter"
        return "book"
    if section_name == "Bolsas" and any(
        marker in normalized for marker in ("fapesp", "cnpq", "capes")
    ):
        return "grant"
    for item_type, keywords in _TYPE_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return item_type
    return fallback_type


def _line_item(
    item_type: str,
    line: str,
    payload: LattesImportInput,
    *,
    confidence: ProfileConfidence = "medium",
) -> ProfileItem:
    source_ref = _best_source_ref(line, payload)
    return _item(
        item_type,
        _title_from_line(line, item_type),
        _short_evidence(line),
        payload,
        source_ref=source_ref,
        confidence=confidence,
        tags=_tags_for_line(line, item_type),
        skills=_skills_for_line(line),
    )


def _item(
    item_type: str,
    title: str,
    evidence: str,
    payload: LattesImportInput,
    *,
    source_ref: str = "",
    confidence: ProfileConfidence = "medium",
    tags: list[str] | None = None,
    skills: list[str] | None = None,
) -> ProfileItem:
    return ProfileItem(
        type=item_type,
        title=title[:240].strip() or _ACADEMIC_TYPE_LABELS.get(item_type, "Evidência acadêmica"),
        description=evidence,
        area=_area_for_text(evidence),
        domain=_domain_for_text(evidence, item_type),
        institution=_institution_hint(evidence),
        organization=_organization_hint(evidence),
        status=_status_hint(evidence),
        start_date=_first_year(evidence),
        end_date=_last_year(evidence),
        tags=tags or [],
        skills=skills or [],
        evidence=evidence,
        source="curriculum_lattes",
        source_ref=source_ref or payload.lattes_id or payload.source_url or payload.orcid or None,
        confidence=confidence,
        confirmed_by_user=False,
        sensitive=False,
    )


def _explicit_identifiers(text: str, payload: LattesImportInput) -> dict[str, str]:
    lattes = payload.lattes_id.strip()
    if not lattes:
        match = _LATTES_URL_RE.search(text) or _LATTES_URL_RE.search(payload.source_url)
        lattes = match.group(1) if match else ""
    orcid = payload.orcid.strip().upper()
    if not orcid:
        match = _ORCID_RE.search(text)
        orcid = match.group(0).upper() if match else ""
    return {"lattes": lattes, "orcid": orcid}


def _best_source_ref(line: str, payload: LattesImportInput) -> str:
    doi = _first_match(_DOI_RE, line)
    if doi:
        return doi
    orcid = _first_match(_ORCID_RE, line)
    if orcid:
        return orcid.upper()
    isbn = _first_match(_ISBN_RE, line)
    if isbn:
        return isbn
    issn = _first_match(_ISSN_RE, line)
    if issn:
        return issn
    return payload.lattes_id or payload.source_url or payload.orcid


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(0).strip().rstrip(".,;") if match else ""


def _identifier_evidence(text: str, identifier: str) -> str:
    if not identifier:
        return ""
    for line in text.splitlines():
        if identifier.lower() in line.lower():
            return _short_evidence(line)
    return ""


def _relevant_lines(lines: list[str], *, max_lines: int = 8) -> list[str]:
    selected = []
    for line in lines:
        cleaned = line.strip(" -\t")
        if len(cleaned) < 4:
            continue
        if _section_name(cleaned):
            continue
        selected.append(cleaned)
        if len(selected) >= max_lines:
            break
    return selected


def _title_from_line(line: str, item_type: str) -> str:
    cleaned = " ".join(line.replace("•", " ").replace("\t", " ").split())
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
    cleaned = re.sub(r"^(?:[12]\d{3}\s*[-–]\s*){1,2}", "", cleaned).strip(" -–")
    if len(cleaned) <= 110:
        return cleaned or _ACADEMIC_TYPE_LABELS.get(item_type, "Evidência acadêmica")
    separators = [". ", " - ", " – ", ": "]
    for separator in separators:
        head = cleaned.split(separator, 1)[0].strip()
        if 12 <= len(head) <= 110:
            return head
    return f"{_ACADEMIC_TYPE_LABELS.get(item_type, 'Evidência acadêmica')}: {cleaned[:120]}"


def _short_evidence(text: str, *, limit: int = 420) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _tags_for_line(line: str, item_type: str) -> list[str]:
    normalized = normalize_text(line)
    tags = [_ACADEMIC_TYPE_LABELS.get(item_type, item_type)]
    for marker, label in {
        "lattes": "Lattes",
        "orcid": "ORCID",
        "doi": "DOI",
        "cnpq": "CNPq",
        "capes": "CAPES",
        "fapesp": "FAPESP",
        "pibic": "PIBIC",
        "pibiti": "PIBITI",
        "extensao": "extensão",
        "laboratorio": "laboratório",
        "publicacao": "publicação",
    }.items():
        if marker in normalized:
            tags.append(label)
    return _unique(tags)


def _skills_for_line(line: str) -> list[str]:
    normalized = normalize_text(line)
    skills = []
    for marker, label in {
        "python": "Python",
        "r ": "R",
        "sql": "SQL",
        "analise de dados": "análise de dados",
        "estatistica": "estatística",
        "laboratorio": "laboratório",
        "docencia": "docência",
        "metodologia": "metodologia científica",
        "geofisica": "geofísica",
        "simulacao": "simulação",
    }.items():
        if marker.strip() in normalized:
            skills.append(label)
    return _unique(skills)


def _area_for_text(text: str) -> str | None:
    normalized = normalize_text(text)
    for marker, area in {
        "geofisica": "Geofísica",
        "ionosfera": "Geofísica",
        "saude": "Saúde",
        "enfermagem": "Saúde",
        "direito": "Direito",
        "educacao": "Educação",
        "engenharia": "Engenharia",
        "quimica": "Química",
        "biologia": "Biologia",
        "artes": "Artes",
        "design": "Design",
        "computacao": "Computação",
    }.items():
        if marker in normalized:
            return area
    return None


def _domain_for_text(text: str, item_type: str) -> str:
    normalized = normalize_text(text)
    for domain, keywords in _DOMAIN_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return domain
    if item_type in {
        "journal_article",
        "conference_paper",
        "publication",
        "book",
        "book_chapter",
    }:
        return "Produção científica"
    if item_type in {"research_project", "scientific_initiation", "research_area", "cnpq_area"}:
        return "Pesquisa acadêmica"
    if item_type in {"extension_project"}:
        return "Extensão universitária"
    if item_type in {"teaching_experience", "monitoring", "teaching_assistant"}:
        return "Docência"
    return "Acadêmico"


def _institution_hint(text: str) -> str | None:
    for marker in ("Universidade", "Instituto", "Faculdade", "Centro Universitário", "UNIVAP"):
        match = re.search(rf"\b{marker}\b[^.;,\n]{{0,80}}", text, flags=re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def _organization_hint(text: str) -> str | None:
    for marker in ("CNPq", "CAPES", "FAPESP", "PIBIC", "PIBITI"):
        if marker.lower() in text.lower():
            return marker
    return None


def _status_hint(text: str) -> str | None:
    normalized = normalize_text(text)
    if any(marker in normalized for marker in ("em andamento", "atual")):
        return "in_progress"
    if any(marker in normalized for marker in ("concluido", "concluida", "finalizado")):
        return "completed"
    return None


def _first_year(text: str) -> str | None:
    years = _YEAR_RE.findall(text)
    return years[0] if years else None


def _last_year(text: str) -> str | None:
    years = _YEAR_RE.findall(text)
    return years[-1] if len(years) > 1 else None


def _has_strong_marker(line: str, item_type: str) -> bool:
    normalized = normalize_text(line)
    if item_type in {"journal_article", "conference_paper", "publication"}:
        return bool(_DOI_RE.search(line) or "doi" in normalized or _YEAR_RE.search(line))
    if item_type in {"orcid", "lattes_identifier"}:
        return True
    return bool(_YEAR_RE.search(line) or _ISBN_RE.search(line) or _ISSN_RE.search(line))


def _dedupe_items(items: list[ProfileItem]) -> list[ProfileItem]:
    unique: list[ProfileItem] = []
    seen: set[str] = set()
    for item in items:
        key = normalize_text(" ".join([item.type, item.title, item.source_ref or ""]))
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _overall_confidence(items: list[ProfileItem], sections: list[str]) -> ProfileConfidence:
    if not items:
        return "low"
    if len(sections) >= 3 and any(item.confidence == "high" for item in items):
        return "high"
    if len(items) >= 2:
        return "medium"
    return items[0].confidence


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        key = normalize_text(cleaned)
        if cleaned and key and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result
