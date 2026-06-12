"""Generate job-search queries for public search engines and specific domains."""

from __future__ import annotations

from modules.core.schemas import JobSearchQuery


def generate_basic_queries(query: JobSearchQuery) -> list[str]:
    """Generate simple multilingual queries from a target profile."""
    role = query.role.strip()
    skills = " ".join(f'"{skill}"' for skill in query.skills[:3])
    seniority = query.seniority.value if query.seniority.value != "unknown" else ""
    modality = query.modality or ""
    location = query.location or ""

    candidates = [
        f'"{role}" "{seniority}" "{modality}" {skills} "{location}"',
        f'"{role}" "vaga aberta" {skills}',
        f'"{role}" "estamos contratando" {skills}',
        f'"{role}" "time crescendo" {skills}',
    ]
    return [item.replace('  ', ' ').strip() for item in candidates if item.strip()]


def generate_domain_queries(query: JobSearchQuery) -> list[str]:
    """Generate domain-specific search queries."""
    role = query.role.strip()
    skills = " ".join(f'"{skill}"' for skill in query.skills[:2])
    domains = [
        "linkedin.com/posts",
        "gupy.io",
        "greenhouse.io",
        "lever.co",
        "ashbyhq.com",
        "inhire.app",
        "ciee.org.br",
        "ciadeestagios.com.br",
    ]
    return [f'site:{domain} "{role}" {skills}'.strip() for domain in domains]


def generate_all_queries(query: JobSearchQuery) -> list[str]:
    """Generate all queries preserving order and removing duplicates."""
    seen: set[str] = set()
    output: list[str] = []
    for item in [*generate_basic_queries(query), *generate_domain_queries(query)]:
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output
