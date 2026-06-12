"""Heuristic job-description parser for the guided local workflow."""

from __future__ import annotations

import re

from modules.core.text_utils import extract_keywords, normalize_text
from modules.schemas.job_posting import JobPostingSchema

SKILL_CATALOG = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Angular",
    "Vue",
    "Node.js",
    "C#",
    "C++",
    "SQL",
    "NoSQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Power BI",
    "Tableau",
    "Excel",
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Git",
    "REST",
    "GraphQL",
    "FastAPI",
    "Django",
    "Flask",
    "Spring",
    "Pytest",
    "Selenium",
    "Scrum",
    "Kanban",
    "Machine Learning",
]
TITLE_LABELS = ("cargo", "vaga", "posição", "posicao", "role", "title")
COMPANY_LABELS = ("empresa", "company", "companhia")
LOCATION_LABELS = ("localização", "localizacao", "local", "location", "cidade")


def _labeled_value(lines: list[str], labels: tuple[str, ...]) -> str:
    for line in lines:
        for label in labels:
            match = re.match(rf"^\s*{label}\s*[:\-]\s*(.+)$", line, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return ""


def _detect_title(lines: list[str]) -> str:
    labeled = _labeled_value(lines, TITLE_LABELS)
    if labeled:
        return labeled
    for line in lines[:5]:
        normalized = normalize_text(line)
        if 2 <= len(line.split()) <= 10 and any(
            term in normalized
            for term in [
                "analista",
                "assistant",
                "assistente",
                "developer",
                "desenvolvedor",
                "engenheiro",
                "engineer",
                "estagio",
                "intern",
                "specialist",
            ]
        ):
            return line.strip("# -*")
    return lines[0].strip("# -*") if lines else ""


def _detect_modality(normalized: str) -> str:
    if any(term in normalized for term in ["remoto", "remote", "home office"]):
        return "remote"
    if any(term in normalized for term in ["hibrido", "hybrid"]):
        return "hybrid"
    if any(term in normalized for term in ["presencial", "onsite", "on-site"]):
        return "onsite"
    return "unknown"


def _detect_salary(text: str) -> tuple[int | None, int | None]:
    contexts = [
        line
        for line in text.splitlines()
        if re.search(r"(R\$|sal[aá]rio|remunera[cç][aã]o|faixa salarial)", line, re.IGNORECASE)
    ]
    if not contexts:
        return None, None
    amounts = re.findall(
        r"(?:R\$\s*)?(\d{1,3}(?:[.\s]\d{3})+|\d{4,6})(?:,\d{2})?",
        "\n".join(contexts),
        flags=re.IGNORECASE,
    )
    values = [int(re.sub(r"\D", "", amount)) for amount in amounts]
    plausible = [value for value in values if 500 <= value <= 500_000]
    if not plausible:
        return None, None
    return min(plausible), max(plausible)


def _detect_contract(normalized: str) -> str:
    terms = [
        ("clt", "CLT"),
        ("pj", "PJ"),
        ("estagio", "estagio"),
        ("internship", "estagio"),
        ("temporario", "temporario"),
        ("freelance", "freelance"),
    ]
    return next((output for term, output in terms if re.search(rf"\b{term}\b", normalized)), "")


def _detect_seniority(normalized: str) -> str:
    terms = [
        ("estagio", "estagio"),
        ("intern", "estagio"),
        ("trainee", "trainee"),
        ("junior", "junior"),
        ("jr", "junior"),
        ("pleno", "pleno"),
        ("mid-level", "pleno"),
        ("senior", "senior"),
        ("sr", "senior"),
        ("lead", "lead"),
        ("especialista", "especialista"),
    ]
    return next((output for term, output in terms if re.search(rf"\b{term}\b", normalized)), "")


def _detect_skills(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [skill for skill in SKILL_CATALOG if normalize_text(skill) in normalized]


def _desired_section(text: str) -> str:
    match = re.search(
        r"(?:desej[aá]vel|diferencial|nice to have|preferred)(.*?)(?:\n\s*\n|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else ""


def parse_job_description(text: str) -> JobPostingSchema:
    """Extract common vacancy facts without requiring an external API."""
    clean_text = (text or "").strip()
    if not clean_text:
        return JobPostingSchema()

    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    normalized = normalize_text(clean_text)
    desired_text = _desired_section(clean_text)
    all_skills = _detect_skills(clean_text)
    desired_skills = _detect_skills(desired_text)
    required_skills = [skill for skill in all_skills if skill not in desired_skills]
    salary_min, salary_max = _detect_salary(clean_text)

    return JobPostingSchema(
        title=_detect_title(lines),
        company=_labeled_value(lines, COMPANY_LABELS),
        location=_labeled_value(lines, LOCATION_LABELS),
        modality=_detect_modality(normalized),
        salary_min=salary_min,
        salary_max=salary_max,
        contract=_detect_contract(normalized),
        seniority=_detect_seniority(normalized),
        required_skills=required_skills,
        desired_skills=desired_skills,
        english_required=bool(
            re.search(
                r"\b(ingles|english)\b.*\b(obrigatorio|required|fluente|fluent)\b", normalized
            )
        ),
        ats_keywords=extract_keywords(clean_text, limit=30),
        raw_text=clean_text,
    )
