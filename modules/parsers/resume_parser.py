"""Resume text and file parser with lightweight PDF/DOCX support."""

from __future__ import annotations

import io
import re
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
    },
    "experiences": {
        "employment",
        "experiencia",
        "experiencia profissional",
        "experiencias",
        "experiencias profissionais",
        "historico profissional",
        "work experience",
    },
    "projects": {
        "portfolio",
        "projetos",
        "projetos academicos",
        "projetos pessoais",
        "projetos profissionais",
        "projects",
    },
    "courses": {"cursos", "cursos complementares", "cursos livres"},
    "certifications": {"certificacoes", "certificados", "certifications"},
    "skills": {
        "competencias",
        "habilidades",
        "skills",
        "skills tecnicas",
        "stack",
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
    "engenheiro",
    "estagio",
    "estagiario",
    "freelancer",
    "monitor",
    "suporte",
}
PROJECT_TERMS = {
    "aplicacao",
    "app",
    "dashboard",
    "projeto academico",
    "projeto pessoal",
    "projeto profissional",
    "sistema",
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
SOFT_SKILL_CATALOG = [
    "Adaptabilidade",
    "Aprendizado contínuo",
    "Autonomia",
    "Comunicação",
    "Criatividade",
    "Liderança",
    "Melhoria contínua",
    "Organização",
    "Proatividade",
    "Resolução de problemas",
    "Trabalho em equipe",
]
LANGUAGE_CATALOG = ["Português", "Inglês", "Espanhol", "Francês", "Alemão", "Italiano"]


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


def _section_marker(line: str) -> tuple[str | None, str]:
    """Return a section name and optional content after an inline heading."""
    stripped = line.strip(" \t#-*•")
    normalized = normalize_text(stripped.rstrip(":"))
    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section, ""
        for alias in aliases:
            match = re.match(rf"^{re.escape(alias)}\s*[:|-]\s*(.+)$", normalized)
            if match:
                separator = re.search(r"[:|-]", stripped)
                trailing = stripped[separator.end() :].strip() if separator else ""
                return section, trailing
    return None, ""


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"header": []}
    sections.update({key: [] for key in SECTION_ALIASES})
    current = "header"
    for line in lines:
        detected, trailing = _section_marker(line)
        if detected:
            current = detected
            if trailing:
                sections[current].append(trailing)
            continue
        sections[current].append(line)
    return sections


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


def _link_by_domain(links: list[str], domain: str) -> str:
    return next((link for link in links if domain in link.lower()), "")


def _detect_city(text: str) -> str:
    match = CITY_PATTERN.search(text)
    return f"{match.group(1).strip()}/{match.group(2)}" if match else ""


def _short_summary(lines: list[str]) -> str:
    """Keep only a few meaningful summary lines, never the whole resume."""
    cleaned = [
        line
        for line in lines
        if not EMAIL_PATTERN.search(line)
        and not PHONE_PATTERN.search(line)
        and not URL_PATTERN.search(line)
        and len(line) >= 20
    ][:3]
    return " ".join(cleaned)[:600].strip()


def _infer_lines(lines: list[str], terms: set[str]) -> list[str]:
    return [
        line
        for line in lines
        if any(term in normalize_text(line) for term in terms) and len(line.split()) >= 2
    ]


def parse_resume_text(text: str, source_type: str = "text") -> ResumeProfileSchema:
    """Extract a reviewable profile from resume text."""
    clean_text = (text or "").strip()
    if not clean_text:
        return ResumeProfileSchema(source_type=source_type)

    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    sections = _split_sections(lines)
    links = _detect_links(clean_text)
    experiences = _unique(
        sections["experiences"] or _infer_lines(lines, ROLE_TERMS)
    )
    projects = _unique(sections["projects"] or _infer_lines(lines, PROJECT_TERMS))
    education = _unique(sections["education"] or _infer_lines(lines, EDUCATION_TERMS))

    return ResumeProfileSchema(
        name=_detect_name(lines),
        email=(EMAIL_PATTERN.search(clean_text).group(0) if EMAIL_PATTERN.search(clean_text) else ""),
        phone=(PHONE_PATTERN.search(clean_text).group(0) if PHONE_PATTERN.search(clean_text) else ""),
        city=_detect_city(clean_text),
        linkedin=_link_by_domain(links, "linkedin.com"),
        github=_link_by_domain(links, "github.com"),
        portfolio=next(
            (
                link
                for link in links
                if any(domain in link.lower() for domain in ["behance", "vercel", "netlify", "github.io"])
            ),
            "",
        ),
        summary=_short_summary(sections["summary"]),
        education=education,
        experiences=experiences,
        projects=projects,
        courses=_unique(sections["courses"]),
        certifications=_unique(sections["certifications"]),
        skills=_detect_skills(clean_text, SKILL_CATALOG),
        soft_skills=_unique(
            [*sections["soft_skills"], *_detect_skills(clean_text, SOFT_SKILL_CATALOG)]
        ),
        languages=_unique(
            [*sections["languages"], *_detect_skills(clean_text, LANGUAGE_CATALOG)]
        ),
        links=links,
        keywords=extract_keywords(clean_text, limit=40),
        raw_text=clean_text,
        source_type=source_type,
    )


def _extract_pdf_text(content: bytes) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Instale pymupdf para ler curriculos PDF.") from exc

    with fitz.open(stream=content, filetype="pdf") as document:
        return "\n".join(page.get_text() for page in document)


def _extract_docx_text(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("Instale python-docx para ler curriculos DOCX.") from exc

    document = Document(io.BytesIO(content))
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
        raise ValueError("Formato nao suportado. Use TXT, PDF ou DOCX.")
    return parse_resume_text(text, source_type=suffix.lstrip("."))
