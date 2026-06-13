"""Resume text and file parser with lightweight PDF/DOCX support."""

from __future__ import annotations

import importlib
import io
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from modules.core.text_utils import extract_keywords, normalize_text
from modules.parsers.job_description_parser import SKILL_CATALOG
from modules.schemas.resume_profile import ResumeProfileSchema

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}")
URL_PATTERN = re.compile(
    r"(?:(?:https?://|www\.)[^\s|)>]+|"
    r"(?:linkedin\.com/in|github\.com|behance\.net|[\w.-]+\.vercel\.app|"
    r"[\w.-]+\.netlify\.app|[\w.-]+\.github\.io)/?[^\s|)>]*)",
    flags=re.IGNORECASE,
)
CITY_PATTERN = re.compile(
    r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ' -]{2,30})\s*[,/-]\s*([A-Z]{2})\b",
)
PERIOD_PATTERN = re.compile(
    r"\b(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-zç]*/?\s*\d{2,4}"
    r"|\b(?:19|20)\d{2}\s*(?:-|–|—|a|até)\s*(?:(?:19|20)\d{2}|atual|presente)"
    r"|\b(?:19|20)\d{2}\b",
    flags=re.IGNORECASE,
)
LIST_SEPARATOR_PATTERN = re.compile(r"\s*(?:,|;|/|\||•|·)\s*")
SKILL_CATEGORY_PREFIX_PATTERN = re.compile(
    r"^\s*(?:"
    r"linguagens?|web(?:\s*/\s*mobile)?|mobile|dados(?:\s*/\s*devops\s*/\s*ferramentas)?|"
    r"devops|bancos?\s+de\s+dados?|hardware(?:\s*/\s*iot)?|iot|ferramentas?|tecnologias?|"
    r"stack|compet[eê]ncias(?:\s+t[eé]cnicas)?|frameworks?"
    r")\s*:\s*",
    flags=re.IGNORECASE,
)


@dataclass
class ResumeSection:
    """A heading and all resume lines that belong to it."""

    name: str
    title: str
    lines: list[str]


SECTION_ALIASES = {
    "summary": {
        "objetivo",
        "objetivo profissional",
        "perfil",
        "perfil profissional",
        "resumo",
        "resumo profissional",
        "summary",
        "profile",
    },
    "education": {
        "academic",
        "educacao",
        "education",
        "formacao",
        "formacao academica",
        "formacao profissional",
        "formacao e cursos",
        "formacao academica e cursos",
    },
    "experiences": {
        "atuacao profissional",
        "employment",
        "experiencia",
        "experiencia profissional",
        "experiencia profissional e tecnica",
        "experiencia tecnica",
        "experiencias",
        "experiencias profissionais",
        "historico profissional",
        "work experience",
    },
    "projects": {
        "portfolio",
        "projetos",
        "projetos academicos",
        "projetos destacados",
        "projetos pessoais",
        "projetos profissionais",
        "projetos relevantes",
        "projetos selecionados",
        "projects",
    },
    "courses": {"cursos", "cursos complementares", "cursos livres"},
    "certifications": {"certificacoes", "certificados", "certifications"},
    "skills": {
        "competencias",
        "competencias tecnicas",
        "habilidades",
        "skills",
        "skills tecnicas",
        "stack",
        "stack tecnica",
        "tecnologias",
    },
    "soft_skills": {"competencias comportamentais", "soft skills", "softskills"},
    "languages": {"idiomas", "languages"},
    "links": {"links", "redes", "redes sociais"},
}
ROLE_TERMS = {
    "analista",
    "assistant",
    "assistente",
    "bolsista",
    "developer",
    "desenvolvedor",
    "eletricista",
    "engenheiro",
    "estagio",
    "estagiario",
    "freelancer",
    "monitor",
    "suporte",
    "tecnico",
}
PROJECT_TERMS = {
    "aplicacao",
    "app",
    "dashboard",
    "plataforma",
    "projeto academico",
    "projeto pessoal",
    "projeto profissional",
    "sistema",
}
PROJECT_DETAIL_LABELS = {
    "atividades",
    "contexto",
    "descricao",
    "destaques",
    "ferramentas",
    "impacto",
    "responsabilidades",
    "resultados",
    "stack",
    "tecnologias",
}
EDUCATION_TERMS = {
    "bacharelado",
    "curso tecnico",
    "engenharia",
    "faculdade",
    "graduacao",
    "tecnologia em",
    "tecnico em",
    "universidade",
}
COURSE_TERMS = {"certificacao", "certificado", "curso", "formacao complementar", "treinamento"}
SOFT_SKILL_CATALOG = [
    "Adaptabilidade",
    "Aprendizado contínuo",
    "Aprendizado rápido",
    "Autonomia",
    "Comunicação",
    "Comunicação técnica",
    "Criatividade",
    "Liderança",
    "Melhoria contínua",
    "Organização",
    "Proatividade",
    "Resolução de problemas",
    "Trabalho em equipe",
]
LANGUAGE_CATALOG = ["Português", "Inglês", "Espanhol", "Francês", "Alemão", "Italiano"]
SKILL_CATEGORY_NAMES = {
    "banco de dados",
    "bancos de dados",
    "competencias",
    "competencias tecnicas",
    "dados",
    "devops",
    "ferramentas",
    "frameworks",
    "hardware",
    "iot",
    "linguagem",
    "linguagens",
    "mobile",
    "stack",
    "tecnologias",
    "web",
}


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = item.strip(" \t-*•|")
        key = normalize_text(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def _section_marker(line: str) -> tuple[str | None, str, str]:
    """Return section name, original heading, and optional inline content."""
    stripped = line.strip(" \t#-*•")
    normalized = normalize_text(stripped.rstrip(":"))
    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section, stripped.rstrip(":"), ""
        for alias in aliases:
            match = re.match(rf"^{re.escape(alias)}\s*[:|-]\s*(.+)$", normalized)
            if match:
                separator = re.search(r"[:|-]", stripped)
                trailing = stripped[separator.end() :].strip() if separator else ""
                title = stripped[: separator.start()].strip() if separator else alias
                return section, title, trailing
    return None, "", ""


def _split_sections(lines: list[str]) -> list[ResumeSection]:
    sections = [ResumeSection(name="header", title="", lines=[])]
    for line in lines:
        detected, title, trailing = _section_marker(line)
        if (
            detected
            and trailing
            and sections[-1].name in {"experiences", "projects"}
            and normalize_text(title) in PROJECT_DETAIL_LABELS
        ):
            sections[-1].lines.append(line)
            continue
        if detected:
            sections.append(ResumeSection(name=detected, title=title, lines=[]))
            if trailing:
                sections[-1].lines.append(trailing)
            continue
        sections[-1].lines.append(line)
    return sections


def _section_lines(sections: list[ResumeSection], name: str) -> list[str]:
    return [line for section in sections if section.name == name for line in section.lines]


def _detect_name(lines: list[str]) -> str:
    for line in lines[:6]:
        candidate = line.strip()
        normalized = normalize_text(candidate)
        if (
            2 <= len(candidate.split()) <= 6
            and not URL_PATTERN.search(candidate)
            and not EMAIL_PATTERN.search(candidate)
            and not PHONE_PATTERN.fullmatch(candidate)
            and not _section_marker(candidate)[0]
            and not any(char.isdigit() for char in candidate)
            and not any(term in normalized for term in ROLE_TERMS | EDUCATION_TERMS)
        ):
            return candidate
    return ""


def _detect_skills(text: str, catalog: list[str]) -> list[str]:
    normalized = normalize_text(text)
    detected = []
    for skill in catalog:
        normalized_skill = normalize_text(skill)
        if re.search(rf"(?<!\w){re.escape(normalized_skill)}(?!\w)", normalized):
            detected.append(skill)
    return _unique(detected)


def _detect_links(text: str) -> list[str]:
    return _unique([link.rstrip(".,;") for link in URL_PATTERN.findall(text)])


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(0) if match else ""


def _link_by_domain(links: list[str], domain: str) -> str:
    return next((link for link in links if domain in link.lower()), "")


def _detect_city(text: str) -> str:
    match = CITY_PATTERN.search(text)
    return f"{match.group(1).strip()}/{match.group(2)}" if match else ""


def _meaningful_lines(lines: list[str]) -> list[str]:
    return [
        line.strip(" \t-*•")
        for line in lines
        if line.strip(" \t-*•")
        and not EMAIL_PATTERN.search(line)
        and not PHONE_PATTERN.search(line)
        and not URL_PATTERN.search(line)
    ]


def _short_summary(
    summary_lines: list[str],
    education: list[str],
    skills: list[str],
) -> str:
    """Return at most three explicit summary lines or a conservative local synthesis."""
    explicit = _meaningful_lines(summary_lines)[:3]
    if explicit:
        return " ".join(explicit)[:600].strip()

    parts: list[str] = []
    if education:
        parts.append(education[0].splitlines()[0])
    if skills:
        parts.append(f"Competências principais: {', '.join(skills[:6])}.")
    return " ".join(parts)[:400].strip()


def _infer_lines(lines: list[str], terms: set[str]) -> list[str]:
    return [
        line
        for line in lines
        if any(term in normalize_text(line) for term in terms) and len(line.split()) >= 2
    ]


def _join_block(lines: list[str]) -> str:
    return "\n".join(_meaningful_lines(lines)).strip()


def _group_blocks(lines: list[str], starts_block: Callable[[str], bool]) -> list[str]:
    """Group heading content, only splitting when a credible new item starts."""
    cleaned = _meaningful_lines(lines)
    if not cleaned:
        return []

    blocks: list[list[str]] = []
    current: list[str] = []
    for line in cleaned:
        if current and starts_block(line):
            blocks.append(current)
            current = []
        current.append(line)
    if current:
        blocks.append(current)
    return _unique([_join_block(block) for block in blocks])


def _starts_experience(line: str) -> bool:
    normalized = normalize_text(line)
    has_role = any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in ROLE_TERMS)
    has_period = bool(PERIOD_PATTERN.search(normalized))
    has_header_separator = bool(re.search(r"\s[-–—|]\s", line))
    return has_period and (has_role or has_header_separator)


def _starts_project(line: str) -> bool:
    normalized = normalize_text(line)
    prefix = line.split(":", 1)[0].strip()
    normalized_prefix = normalize_text(prefix)
    named_project = (
        ":" in line
        and 1 <= len(prefix.split()) <= 8
        and normalized_prefix not in PROJECT_DETAIL_LABELS
    )
    explicit_project = any(term in normalized for term in PROJECT_TERMS)
    return named_project or (explicit_project and len(line.split()) <= 18)


def _starts_education(line: str) -> bool:
    normalized = normalize_text(line)
    return any(term in normalized for term in EDUCATION_TERMS)


def _starts_course(line: str) -> bool:
    normalized = normalize_text(line)
    return any(term in normalized for term in COURSE_TERMS)


def _split_list_items(lines: list[str], *, split_and: bool = False) -> list[str]:
    items: list[str] = []
    for line in _meaningful_lines(lines):
        fragments = LIST_SEPARATOR_PATTERN.split(line)
        if split_and:
            fragments = [
                part
                for fragment in fragments
                for part in re.split(r"\s+(?:e|and)\s+", fragment, flags=re.IGNORECASE)
            ]
        items.extend(fragment.strip(" .:-") for fragment in fragments)
    return _unique(items)


def _strip_skill_category_prefix(line: str) -> str:
    return SKILL_CATEGORY_PREFIX_PATTERN.sub("", line, count=1).strip()


def _is_technical_skill_chip(item: str) -> bool:
    normalized = normalize_text(item)
    soft_skills = {normalize_text(skill) for skill in SOFT_SKILL_CATALOG}
    languages = {normalize_text(language) for language in LANGUAGE_CATALOG}
    return bool(
        normalized
        and normalized not in SKILL_CATEGORY_NAMES
        and normalized not in soft_skills
        and normalized not in languages
        and len(item.split()) <= 4
        and len(item) <= 40
    )


def _technical_skill_chips(lines: list[str], clean_text: str) -> list[str]:
    chips = []
    cleaned_lines = [_strip_skill_category_prefix(line) for line in lines]
    for item in _split_list_items(cleaned_lines):
        item = _strip_skill_category_prefix(item)
        if _is_technical_skill_chip(item):
            chips.append(item)
        else:
            chips.extend(_detect_skills(item, SKILL_CATALOG))
    return _unique([*chips, *_detect_skills(clean_text, SKILL_CATALOG)])


def _combined_education_and_courses(
    sections: list[ResumeSection],
) -> tuple[list[str], list[str]]:
    education_lines = _section_lines(sections, "education")
    education = _group_blocks(
        [line for line in education_lines if not _starts_course(line) or _starts_education(line)],
        _starts_education,
    )
    courses = _group_blocks(
        [line for line in education_lines if _starts_course(line) and not _starts_education(line)],
        _starts_course,
    )
    courses.extend(_group_blocks(_section_lines(sections, "courses"), _starts_course))
    return _unique(education), _unique(courses)


def parse_resume_text(text: str, source_type: str = "text") -> ResumeProfileSchema:
    """Extract a reviewable profile from resume text."""
    clean_text = (text or "").strip()
    if not clean_text:
        return ResumeProfileSchema(source_type=source_type)

    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    sections = _split_sections(lines)
    links = _detect_links(clean_text)
    experience_lines = _section_lines(sections, "experiences")
    project_lines = _section_lines(sections, "projects")
    education, courses = _combined_education_and_courses(sections)

    experiences = _group_blocks(experience_lines, _starts_experience)
    projects = _group_blocks(project_lines, _starts_project)
    if not experiences:
        experiences = _unique(_infer_lines(lines, ROLE_TERMS))
    if not projects:
        projects = _unique(_infer_lines(lines, PROJECT_TERMS))
    if not education:
        education = _unique(_infer_lines(lines, EDUCATION_TERMS))

    skills = _technical_skill_chips(_section_lines(sections, "skills"), clean_text)
    soft_skills = _unique(
        [
            *_split_list_items(_section_lines(sections, "soft_skills"), split_and=True),
            *_detect_skills(clean_text, SOFT_SKILL_CATALOG),
        ]
    )

    return ResumeProfileSchema(
        name=_detect_name(lines),
        email=_first_match(EMAIL_PATTERN, clean_text),
        phone=_first_match(PHONE_PATTERN, clean_text),
        city=_detect_city(clean_text),
        linkedin=_link_by_domain(links, "linkedin.com"),
        github=_link_by_domain(links, "github.com"),
        portfolio=next(
            (
                link
                for link in links
                if any(
                    domain in link.lower()
                    for domain in ["behance", "vercel", "netlify", "github.io"]
                )
            ),
            "",
        ),
        summary=_short_summary(_section_lines(sections, "summary"), education, skills),
        education=education,
        experiences=experiences,
        projects=projects,
        courses=courses,
        certifications=_group_blocks(_section_lines(sections, "certifications"), _starts_course),
        skills=skills,
        soft_skills=soft_skills,
        languages=_unique(
            [
                *_split_list_items(_section_lines(sections, "languages")),
                *_detect_skills(clean_text, LANGUAGE_CATALOG),
            ]
        ),
        links=links,
        keywords=extract_keywords(clean_text, limit=40),
        raw_text=clean_text,
        source_type=source_type,
    )


def _extract_pdf_text(content: bytes) -> str:
    try:
        fitz = importlib.import_module("fitz")
    except ImportError as exc:
        raise RuntimeError("Instale pymupdf para ler currículos PDF.") from exc

    with fitz.open(stream=content, filetype="pdf") as document:
        return "\n".join(page.get_text() for page in document)


def _extract_docx_text(content: bytes) -> str:
    try:
        document_module = importlib.import_module("docx")
    except ImportError as exc:
        raise RuntimeError("Instale python-docx para ler currículos DOCX.") from exc

    document = document_module.Document(io.BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def parse_resume_file(filename: str, content: bytes) -> ResumeProfileSchema:
    """Parse a TXT, PDF, or DOCX resume supplied as bytes."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        text = content.decode("utf-8", errors="replace")
    elif suffix == ".pdf":
        text = _extract_pdf_text(content)
    elif suffix == ".docx":
        text = _extract_docx_text(content)
    else:
        raise ValueError("Formato não suportado. Use TXT, PDF ou DOCX.")
    return parse_resume_text(text, source_type=suffix.lstrip("."))
