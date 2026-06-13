"""URL safety and robots.txt checks."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from modules.scraping.schemas import SourceSafety

AUTH_MARKERS = ("/login", "/signin", "/auth", "/checkpoint", "/session")


def detect_source_type(url: str) -> str:
    """Infer a useful source type from a public URL."""
    lowered = url.lower()
    if lowered.endswith((".rss", ".xml", ".atom")) or "feed" in lowered:
        return "rss"
    if any(term in lowered for term in ("/jobs/", "/job/", "/vaga/", "/vagas/")):
        return "manual_url"
    if any(term in lowered for term in ("careers", "carreiras", "trabalhe-conosco")):
        return "company_career_page"
    return "generic_public_page"


def inspect_source_safety(url: str) -> SourceSafety:
    """Reject authenticated or non-public URLs before any request."""
    parsed = urlparse(url.strip())
    domain = parsed.netloc.lower()
    is_linkedin = domain == "linkedin.com" or domain.endswith(".linkedin.com")
    authentication_required = any(marker in parsed.path.lower() for marker in AUTH_MARKERS)
    allowed = (
        parsed.scheme in {"http", "https"}
        and bool(domain)
        and not authentication_required
        and not is_linkedin
    )
    warning = ""
    if authentication_required:
        warning = (
            "A URL parece exigir autenticação. A coleta pública não é permitida; "
            "use o modo Navegador autenticado autorizado quando aplicável."
        )
    elif is_linkedin:
        warning = (
            "Para LinkedIn, selecione 'Navegador autenticado autorizado', abra o navegador "
            "dedicado e faça login manualmente nele."
        )
    elif not allowed:
        warning = "Informe uma URL pública HTTP ou HTTPS."
    return SourceSafety(
        allowed=allowed,
        domain=domain,
        detected_type=detect_source_type(url),
        robots_status="pendente" if allowed else "bloqueado",
        authentication_required=authentication_required,
        warning=warning,
    )


def robots_allows(
    url: str,
    user_agent: str,
    *,
    reader_factory: Callable[[], RobotFileParser] = RobotFileParser,
) -> bool:
    """Return whether robots.txt allows collection for the identifiable agent."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = reader_factory()
    parser.set_url(robots_url)
    try:
        parser.read()
    except OSError:
        return True
    return parser.can_fetch(user_agent, url)
