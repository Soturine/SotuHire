"""Collect authorized opportunities through an already authenticated browser."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urljoin, urlparse

from modules.scraping.browser_session import inspect_browser_session
from modules.scraping.connectors.manual_url import opportunity_from_text
from modules.scraping.dedupe import deduplicate_opportunities, normalize_url
from modules.scraping.schemas import CollectionResult, ScrapingSource

LOGGER = logging.getLogger("sotuhire.scraping.authenticated")

CHECKPOINT_MARKERS = (
    "/authwall",
    "/challenge",
    "/checkpoint",
    "/login",
    "captcha",
)
CHECKPOINT_SELECTOR = (
    'iframe[src*="captcha"], [id*="captcha"], [class*="captcha"], '
    'form[action*="/checkpoint"], form[action*="/login"]'
)

LINKEDIN_JOBS_SELECTORS = {
    "link": 'a[href*="/jobs/view/"]',
    "title": (
        ".job-details-jobs-unified-top-card__job-title h1, "
        ".job-details-jobs-unified-top-card__job-title, h1"
    ),
    "content": (
        ".jobs-description-content__text, .jobs-description, "
        ".job-details-about-the-job-module__description, main"
    ),
    "next": (
        'button[aria-label*="Next"], button[aria-label*="Próxima"], button[aria-label*="Avançar"]'
    ),
}

LINKEDIN_POSTS_SELECTORS = {
    "item": 'div.feed-shared-update-v2, div[data-urn*="activity"]',
    "item_link": 'a[href*="/feed/update/"], a[href*="/posts/"]',
}


@dataclass(frozen=True)
class BrowserCapture:
    """Visible opportunity content captured from one authenticated page or card."""

    url: str
    title: str
    text: str


class AuthenticatedCrawler(Protocol):
    """Small injectable browser crawler contract."""

    def crawl(self, source: ScrapingSource) -> list[BrowserCapture]: ...


def selectors_for_source(source: ScrapingSource) -> dict[str, str]:
    """Return platform defaults merged with explicitly configured selectors."""
    parsed = urlparse(source.url)
    path = parsed.path.lower()
    selectors: dict[str, str] = {}
    if parsed.netloc.lower().endswith("linkedin.com"):
        selectors = (
            LINKEDIN_POSTS_SELECTORS.copy()
            if "/feed" in path or "/posts" in path or "/search/results/content" in path
            else LINKEDIN_JOBS_SELECTORS.copy()
        )
    selectors.update({key: value for key, value in source.selectors.items() if value.strip()})
    if not selectors.get("item") and not selectors.get("link"):
        raise ValueError("A fonte autenticada precisa de seletores 'item' ou 'link' configurados.")
    return selectors


def _checkpoint_detected(url: str) -> bool:
    normalized = url.lower()
    return any(marker in normalized for marker in CHECKPOINT_MARKERS)


class PlaywrightAuthenticatedCrawler:
    """Use a user-started Chromium CDP session without automating login."""

    def crawl(self, source: ScrapingSource) -> list[BrowserCapture]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Instale requirements-scraping.txt para usar o navegador autenticado."
            ) from exc

        selectors = selectors_for_source(source)
        session = inspect_browser_session(source.browser_cdp_url)
        if not session.available:
            raise RuntimeError(
                "Navegador autenticado desconectado. Clique em 'Abrir navegador para login' "
                "e faça login manualmente antes de coletar."
            )
        captures: list[BrowserCapture] = []
        links: list[str] = []
        seen_links: set[str] = set()
        LOGGER.info(
            "Starting authorized browser crawl domain=%s max_items=%s max_pages=%s",
            urlparse(source.url).netloc.lower(),
            source.max_items,
            source.max_pages,
        )

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(source.browser_cdp_url, timeout=10_000)
            if not browser.contexts:
                raise RuntimeError("Nenhum contexto Chromium autenticado foi encontrado via CDP.")
            context = browser.contexts[0]
            listing_page = context.new_page()
            detail_page = None
            try:
                listing_page.goto(source.url, wait_until="domcontentloaded", timeout=30_000)
                self._ensure_authenticated(listing_page)
                for page_number in range(1, source.max_pages + 1):
                    self._wait(listing_page, source.delay_seconds)
                    self._ensure_authenticated(listing_page)
                    self._capture_visible_items(
                        listing_page,
                        selectors,
                        source,
                        captures,
                    )
                    self._collect_visible_links(
                        listing_page,
                        selectors,
                        links,
                        seen_links,
                        source.max_items,
                    )
                    LOGGER.info(
                        "Authorized browser crawl progress page=%s captures=%s links=%s",
                        page_number,
                        len(captures),
                        len(links),
                    )
                    if len(captures) >= source.max_items or len(links) >= source.max_items:
                        break
                    if not self._advance_listing(listing_page, selectors):
                        break

                if links and len(captures) < source.max_items:
                    detail_page = context.new_page()
                    for link in links[: source.max_items - len(captures)]:
                        try:
                            detail_page.goto(link, wait_until="domcontentloaded", timeout=30_000)
                            self._wait(detail_page, source.delay_seconds)
                        except Exception:
                            LOGGER.warning(
                                "Skipping authenticated detail page url=%s",
                                link,
                                exc_info=True,
                            )
                            continue
                        self._ensure_authenticated(detail_page)
                        text = self._first_text(detail_page, selectors.get("content", "main"))
                        if text:
                            captures.append(
                                BrowserCapture(
                                    url=detail_page.url,
                                    title=self._first_text(
                                        detail_page, selectors.get("title", "h1")
                                    ),
                                    text=text,
                                )
                            )
            finally:
                if detail_page is not None:
                    detail_page.close()
                listing_page.close()
        LOGGER.info("Authorized browser crawl finished captures=%s", len(captures))
        return captures[: source.max_items]

    @staticmethod
    def _wait(page: Any, delay_seconds: float) -> None:
        page.wait_for_timeout(int(delay_seconds * 1000))

    @staticmethod
    def _ensure_authenticated(page: Any) -> None:
        checkpoints = page.locator(CHECKPOINT_SELECTOR)
        checkpoint_visible = any(
            checkpoints.nth(index).is_visible() for index in range(min(checkpoints.count(), 10))
        )
        if _checkpoint_detected(page.url) or checkpoint_visible:
            raise RuntimeError(
                "A plataforma solicitou login, checkpoint ou CAPTCHA. "
                "Resolva manualmente no navegador antes de tentar novamente."
            )

    @staticmethod
    def _first_text(page: Any, selector: str) -> str:
        if not selector:
            return ""
        for candidate in selector.split(","):
            locator = page.locator(candidate.strip())
            for index in range(min(locator.count(), 5)):
                try:
                    item = locator.nth(index)
                    if item.is_visible():
                        return item.inner_text(timeout=5_000).strip()
                except Exception:
                    LOGGER.debug("Skipping detached authenticated content", exc_info=True)
        return ""

    @staticmethod
    def _capture_visible_items(
        page: Any,
        selectors: dict[str, str],
        source: ScrapingSource,
        captures: list[BrowserCapture],
    ) -> None:
        item_selector = selectors.get("item", "")
        if not item_selector:
            return
        items = page.locator(item_selector)
        existing = {capture.text for capture in captures}
        for index in range(items.count()):
            if len(captures) >= source.max_items:
                return
            try:
                item = items.nth(index)
                text = item.inner_text(timeout=5_000).strip()
                if len(text) < 40 or text in existing:
                    continue
                link = page.url
                item_link_selector = selectors.get("item_link", "")
                if item_link_selector:
                    item_links = item.locator(item_link_selector)
                    href = item_links.first.get_attribute("href") if item_links.count() else ""
                    if href:
                        link = urljoin(page.url, href)
                captures.append(
                    BrowserCapture(
                        url=link,
                        title=text.splitlines()[0][:180],
                        text=text,
                    )
                )
                existing.add(text)
            except Exception:
                LOGGER.debug("Skipping detached authenticated listing item", exc_info=True)

    @staticmethod
    def _collect_visible_links(
        page: Any,
        selectors: dict[str, str],
        links: list[str],
        seen_links: set[str],
        max_items: int,
    ) -> None:
        link_selector = selectors.get("link", "")
        if not link_selector:
            return
        locators = page.locator(link_selector)
        for index in range(locators.count()):
            try:
                href = locators.nth(index).get_attribute("href")
                absolute = urljoin(page.url, href) if href else ""
                identity = normalize_url(absolute) if absolute else ""
                if identity and identity not in seen_links:
                    links.append(absolute)
                    seen_links.add(identity)
            except Exception:
                LOGGER.debug("Skipping detached authenticated listing link", exc_info=True)
            if len(links) >= max_items:
                return

    @staticmethod
    def _advance_listing(page: Any, selectors: dict[str, str]) -> bool:
        next_selector = selectors.get("next", "")
        if next_selector:
            buttons = page.locator(next_selector)
            for index in range(buttons.count()):
                try:
                    button = buttons.nth(index)
                    if button.is_visible() and button.is_enabled():
                        button.click()
                        return True
                except Exception:
                    LOGGER.debug("Skipping detached authenticated next button", exc_info=True)
        previous_height = page.evaluate("document.body.scrollHeight")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1_000)
        return page.evaluate("document.body.scrollHeight") > previous_height


class AuthenticatedBrowserConnector:
    """Normalize captures from an authorized, already authenticated browser session."""

    def __init__(
        self,
        client: object | None = None,
        crawler: AuthenticatedCrawler | None = None,
    ) -> None:
        del client
        self.crawler = crawler or PlaywrightAuthenticatedCrawler()

    def collect(self, source: ScrapingSource) -> CollectionResult:
        if not source.authorized_use:
            return CollectionResult(
                source=source,
                failures=["Confirme a autorização desta fonte antes da coleta autenticada."],
                authenticated_browser=True,
            )
        try:
            captures = self.crawler.crawl(source)
            opportunities = [
                opportunity_from_text(
                    capture.text,
                    source=source.name,
                    source_url=capture.url,
                    title_hint=capture.title,
                    confidence=0.9,
                )
                for capture in captures
            ]
            opportunities, duplicate_count = deduplicate_opportunities(opportunities)
            return CollectionResult(
                source=source,
                opportunities=opportunities,
                new_count=len(opportunities),
                duplicate_count=duplicate_count,
                scraping_performed=True,
                authenticated_browser=True,
            )
        except Exception as exc:
            LOGGER.exception("Authorized browser crawl failed")
            return CollectionResult(
                source=source,
                failures=[str(exc)],
                authenticated_browser=True,
            )
