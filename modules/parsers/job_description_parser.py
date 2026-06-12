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
TITLE_LABELS = ("cargo", "vaga", "posicao", "role", "title")
COMPANY_LABELS = ("empresa", "company", "companhia")
LOCATION_LABELS = ("localizacao", "local", "location", "cidade")
BENEFIT_TERMS = {
    "Auxílio home office": ("auxilio home office", "ajuda de custo home office"),
    "Gympass/Wellhub": ("gympass", "wellhub"),
    "Participação nos lucros": ("plr", "participacao nos lucros"),
    "Plano de saúde": ("plano de saude", "assistencia medica"),
    "Plano odontológico": ("plano odontologico", "assistencia odontologica"),
    "Seguro de vida": ("seguro de vida",),
    "Vale-alimentação": ("vale alimentacao", "va"),
    "Vale-refeição": ("vale refeicao", "vr"),
    "Vale-transporte": ("vale transporte", "vt"),
}


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _labeled_value(lines: list[str], labels: tuple[str, ...]) -> str:
    for line in lines:
        normalized = normalize_text(line)
        for label in labels:
            match = re.match(rf"^\s*{label}\s*[:\-]\s*(.+)$", normalized)
            if match:
                separator = re.search(r"[:\-]", line)
                return line[separator.end() :].strip() if separator else match.group(1).strip()
    return ""


def _detect_title(lines: list[str]) -> str:
    labeled = _labeled_value(lines, TITLE_LABELS)
    if labeled:
        return labeled
    role_terms = (
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
    )
    for line in lines[:6]:
        normalized = normalize_text(line)
        if 2 <= len(line.split()) <= 12 and any(term in normalized for term in role_terms):
            return line.strip("# -*")
    return lines[0].strip("# -*") if lines else ""


def _detect_modality(normalized: str) -> str:
    if any(term in normalized for term in ["remoto", "remota", "remote", "home office"]):
        return "remote"
    if any(term in normalized for term in ["hibrido", "hibrida", "hybrid"]):
        return "hybrid"
    if any(term in normalized for term in ["presencial", "onsite", "on-site"]):
        return "onsite"
    return "unknown"


def _detect_salary(text: str) -> tuple[int | None, int | None]:
    contexts = [
        line
        for line in text.splitlines()
        if re.search(
            r"(R\$|sal[aá]rio|remunera[cç][aã]o|faixa salarial)",
            line,
            re.IGNORECASE,
        )
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
    return (min(plausible), max(plausible)) if plausible else (None, None)


def _detect_contract(normalized: str) -> str:
    terms = [
        ("clt", "CLT"),
        ("pj", "PJ"),
        ("estagio", "estagio"),
        ("internship", "estagio"),
        ("trainee", "trainee"),
        ("temporario", "temporario"),
        ("freelancer", "freelance"),
        ("freelance", "freelance"),
        ("freela", "freelance"),
    ]
    return next((output for term, output in terms if re.search(rf"\b{term}\b", normalized)), "")


def _detect_seniority(normalized: str) -> str:
    terms = [
        ("estagio", "estagio"),
        ("estagiario", "estagio"),
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
    return [
        skill
        for skill in SKILL_CATALOG
        if re.search(rf"(?<!\w){re.escape(normalize_text(skill))}(?!\w)", normalized)
    ]


def _desired_section(text: str) -> str:
    match = re.search(
        r"(?:desej[aá]vel|diferencial|nice to have|preferred)\s*:?(.*?)(?:\n\s*\n|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else ""


def _detect_benefits(normalized: str) -> list[str]:
    searchable = re.sub(r"[-_/]", " ", normalized)
    return [
        label
        for label, terms in BENEFIT_TERMS.items()
        if any(re.search(rf"\b{re.escape(term)}\b", searchable) for term in terms)
    ]


def _missing_data_risks(job: JobPostingSchema) -> list[str]:
    checks = [
        (job.title, "Cargo não informado."),
        (job.company, "Empresa não informada."),
        (job.location, "Localização não informada."),
        (job.modality != "unknown", "Modalidade não informada."),
        (job.contract, "Tipo de contrato não informado."),
        (job.salary_min is not None, "Faixa salarial não informada."),
    ]
    return [message for value, message in checks if not value]


def parse_job_description(text: str) -> JobPostingSchema:
    """Extract common vacancy facts without requiring an external API."""
    clean_text = (text or "").strip()
    if not clean_text:
        return JobPostingSchema(risk_flags=["Descrição da vaga vazia."])

    lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
    normalized = normalize_text(clean_text)
    desired_skills = _detect_skills(_desired_section(clean_text))
    required_skills = [
        skill for skill in _detect_skills(clean_text) if skill not in desired_skills
    ]
    salary_min, salary_max = _detect_salary(clean_text)
    job = JobPostingSchema(
        title=_detect_title(lines),
        company=_labeled_value(lines, COMPANY_LABELS),
        location=_labeled_value(lines, LOCATION_LABELS),
        modality=_detect_modality(normalized),
        salary_min=salary_min,
        salary_max=salary_max,
        contract=_detect_contract(normalized),
        seniority=_detect_seniority(normalized),
        required_skills=_unique(required_skills),
        desired_skills=_unique(desired_skills),
        english_required=bool(
            re.search(
                r"\b(ingles|english)\b.*\b(obrigatorio|required|fluente|fluent)\b",
                normalized,
            )
        ),
        benefits=_detect_benefits(normalized),
        ats_keywords=extract_keywords(clean_text, limit=30),
        raw_text=clean_text,
    )
    return job.model_copy(update={"risk_flags": _missing_data_risks(job)})
