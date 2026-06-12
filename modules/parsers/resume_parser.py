"""Resume text and file parser with lightweight PDF/DOCX support."""

from __future__ import annotations

import io
import re
from pathlib import Path

from modules.core.text_utils import extract_keywords, normalize_text
from modules.parsers.job_description_parser import SKILL_CATALOG
from modules.schemas.resume_profile import ResumeProfileSchema

URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s)>]+", flags=re.IGNORECASE)
SECTION_ALIASES = {
    "summary": {"resumo", "perfil", "objetivo", "summary", "profile"},
    "education": {"educacao", "formacao", "education", "academic"},
    "experiences": {"experiencia", "experiencias", "experience", "employment", "work"},
    "projects": {"projetos", "projects", "portfolio"},
    "skills": {"skills", "habilidades", "competencias", "tecnologias", "stack"},
}


def _section_name(line: str) -> str | None:
    normalized = normalize_text(line.strip(":#- "))
    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section
    return None


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {key: [] for key in SECTION_ALIASES}
    current = "summary"
    for line in lines:
        detected = _section_name(line)
        if detected:
            current = detected
            continue
        sections[current].append(line)
    return sections


def _detect_name(lines: list[str]) -> str:
    for line in lines[:5]:
        candidate = line.strip()
        if (
            2 <= len(candidate.split()) <= 6
            and not URL_PATTERN.search(candidate)
            and "@" not in candidate
            and not _section_name(candidate)
        ):
            return candidate
    return ""


def _detect_skills(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [skill for skill in SKILL_CATALOG if normalize_text(skill) in normalized]


def parse_resume_text(text: str, source_type: str = "text") -> ResumeProfileSchema:
    """Extract a reviewable profile from resume text."""
    clean_text = (text or "").strip()
    if not clean_text:
        return ResumeProfileSchema(source_type=source_type)

    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    sections = _split_sections(lines)
    return ResumeProfileSchema(
        name=_detect_name(lines),
        summary=" ".join(sections["summary"][:4]),
        education=sections["education"],
        experiences=sections["experiences"],
        projects=sections["projects"],
        skills=_detect_skills(clean_text),
        links=URL_PATTERN.findall(clean_text),
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
