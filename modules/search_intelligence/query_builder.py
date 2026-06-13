"""Build practical manual search queries from reviewed career intent."""

from __future__ import annotations

from modules.core.text_utils import normalize_text
from modules.search_intelligence.schemas import SearchStrategyInput

SENIORITY_TERMS = {
    "estagio": "estágio",
    "internship": "estágio",
    "junior": "júnior",
    "trainee": "trainee",
    "pleno": "pleno",
    "mid": "pleno",
    "senior": "sênior",
}
MODALITY_TERMS = {
    "remote": "remoto",
    "hybrid": "híbrido",
    "onsite": "presencial",
}


def _compact(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def build_search_queries(strategy: SearchStrategyInput, limit: int = 8) -> list[str]:
    """Generate deduplicated queries without making any network request."""
    role = strategy.target_role.strip()
    skills = strategy.skills[:3]
    seniority = SENIORITY_TERMS.get(normalize_text(strategy.seniority), strategy.seniority)
    modality = MODALITY_TERMS.get(normalize_text(strategy.modality), strategy.modality)
    base = _compact([role, seniority, *skills[:2], modality, strategy.location])

    candidates = [
        f'"{base}"',
        f'"{_compact([role, seniority, skills[0] if skills else "", modality])}"',
        f'"{_compact([role, "vaga aberta", *skills[:2]])}"',
        f'"{_compact([role, "estamos contratando", seniority])}"',
        f'site:linkedin.com/posts "{role}" "{seniority}"',
        f'site:gupy.io "{role}" "{seniority}"',
        f'site:greenhouse.io "{role}" "{strategy.location or "Brazil"}"',
        f'site:lever.co "{role}" "{skills[0] if skills else seniority}"',
    ]
    candidates.extend(
        f'site:{company} "{role}" "{seniority}"'
        for company in strategy.target_companies
        if "." in company
    )
    output: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        cleaned = _compact(candidate.split())
        key = normalize_text(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output[:limit]
