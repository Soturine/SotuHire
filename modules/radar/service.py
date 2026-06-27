"""Local Job Radar service for public feeds, safe source adapters, and alerts."""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from modules.core.collection_method import CollectionMethod
from modules.core.opportunity_identity import normalize_opportunity_url
from modules.core.text_utils import normalize_text
from modules.parsers.job_description_parser import parse_job_description
from modules.radar.models import (
    JobWishlist,
    RadarAlert,
    RadarAlertStatus,
    RadarMatch,
    RadarResult,
    RadarResultStatus,
    RadarRun,
    RadarSource,
    RadarSourceStatus,
    RadarSourceType,
    RadarStats,
    SavedSearch,
    SourceAdapter,
    utc_now,
)
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.scraping.client import ScrapingClient
from modules.scraping.connectors.manual_url import ManualUrlConnector
from modules.scraping.connectors.rss_feed import RssFeedConnector
from modules.scraping.schemas import CollectionResult, ScrapedOpportunity, ScrapingSource
from modules.sources.imports import SourceImportService, SourceOrigin
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker

MAX_SOURCES_PER_RUN = 10
MAX_RESULTS_PER_SOURCE = 50
MAX_DESCRIPTION_CHARS = 20_000


class RadarState(BaseModel):
    """All local radar state persisted in one JSON document."""

    model_config = ConfigDict(extra="forbid")

    wishlists: list[JobWishlist] = Field(default_factory=list)
    saved_searches: list[SavedSearch] = Field(default_factory=list)
    sources: list[RadarSource] = Field(default_factory=list)
    runs: list[RadarRun] = Field(default_factory=list)
    results: list[RadarResult] = Field(default_factory=list)
    alerts: list[RadarAlert] = Field(default_factory=list)


class RadarStore:
    """Atomic JSON store for local radar state."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.path = Path(path) if path is not None else base / "radar" / "radar.json"

    def load(self) -> RadarState:
        """Read persisted radar state."""
        if not self.path.exists():
            return RadarState()
        try:
            return RadarState.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return RadarState()

    def save(self, state: RadarState) -> RadarState:
        """Write radar state atomically."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return state


class JobRadarService:
    """Application service for safe local Job Radar workflows."""

    def __init__(
        self,
        *,
        store: RadarStore | None = None,
        scraping_client: ScrapingClient | None = None,
        source_imports: SourceImportService | None = None,
        tracker: JobTracker | None = None,
    ) -> None:
        self.store = store or RadarStore()
        self.scraping_client = scraping_client or ScrapingClient(
            timeout_seconds=6,
            max_bytes=750_000,
        )
        self.source_imports = source_imports or SourceImportService()
        self.tracker = tracker or JobTracker(LocalStore())

    def adapters(self) -> list[SourceAdapter]:
        """Return documented adapter support."""
        return [
            SourceAdapter(
                source_type="public_feed",
                adapter_name="RSS/Atom publico",
                notes="Refresh manual, limitado e com revisao humana.",
            ),
            SourceAdapter(
                source_type="manual_public_page",
                adapter_name="Pagina publica simples",
                notes="Leitura pontual, sem login, sem insistir em bloqueios.",
            ),
            SourceAdapter(
                source_type="official_api",
                adapter_name="API oficial planejada",
                supported=False,
                notes="Estrutura segura; conector real depende de contrato oficial documentado.",
            ),
            SourceAdapter(
                source_type="recurring_csv_json",
                adapter_name="CSV/JSON recorrente planejado",
                supported=False,
                notes="Use importacao manual ate existir agendamento local explicito.",
            ),
        ]

    def list_wishlists(self) -> list[JobWishlist]:
        """List wishlists newest first."""
        return sorted(self.store.load().wishlists, key=lambda item: item.updated_at, reverse=True)

    def create_wishlist(self, wishlist: JobWishlist) -> JobWishlist:
        """Create a wishlist."""
        state = self.store.load()
        state.wishlists.append(
            wishlist.model_copy(update={"created_at": utc_now(), "updated_at": utc_now()})
        )
        self.store.save(state)
        return state.wishlists[-1]

    def update_wishlist(self, wishlist_id: str, updates: dict[str, object]) -> JobWishlist:
        """Patch one wishlist."""
        state = self.store.load()
        for index, item in enumerate(state.wishlists):
            if item.id == wishlist_id:
                cleaned = {key: value for key, value in updates.items() if value is not None}
                updated = item.model_copy(update={**cleaned, "updated_at": utc_now()})
                state.wishlists[index] = updated
                self.store.save(state)
                return updated
        raise KeyError("Wishlist nao encontrada.")

    def delete_wishlist(self, wishlist_id: str) -> JobWishlist:
        """Deactivate one wishlist without deleting history."""
        return self.update_wishlist(wishlist_id, {"is_active": False})

    def list_sources(self) -> list[RadarSource]:
        """List configured radar sources newest first."""
        return sorted(self.store.load().sources, key=lambda item: item.updated_at, reverse=True)

    def create_source(self, source: RadarSource) -> RadarSource:
        """Create one radar source."""
        state = self.store.load()
        status = _default_source_status(source.source_type, source.status)
        created = source.model_copy(
            update={"status": status, "created_at": utc_now(), "updated_at": utc_now()}
        )
        state.sources.append(created)
        self.store.save(state)
        return created

    def update_source(self, source_id: str, updates: dict[str, object]) -> RadarSource:
        """Patch one radar source."""
        state = self.store.load()
        for index, item in enumerate(state.sources):
            if item.id == source_id:
                cleaned = {key: value for key, value in updates.items() if value is not None}
                updated = item.model_copy(update={**cleaned, "updated_at": utc_now()})
                state.sources[index] = updated
                self.store.save(state)
                return updated
        raise KeyError("Fonte do Radar nao encontrada.")

    def delete_source(self, source_id: str) -> RadarSource:
        """Disable one radar source without deleting history."""
        return self.update_source(source_id, {"is_active": False, "status": "disabled"})

    def run(
        self,
        *,
        source_ids: list[str] | None = None,
        wishlist_id: str = "",
        resume_text: str = "",
        keywords: list[str] | None = None,
        use_ai: bool = False,
        ai_enricher: Callable[[RadarResult, JobWishlist], dict[str, object]] | None = None,
    ) -> tuple[RadarRun, list[RadarResult], list[RadarAlert], list[str]]:
        """Execute one manual bounded radar run."""
        state = self.store.load()
        started = time.perf_counter()
        wanted_sources = set(source_ids or [])
        sources = [
            source
            for source in state.sources
            if source.is_active and (not wanted_sources or source.id in wanted_sources)
        ][:MAX_SOURCES_PER_RUN]
        wishlist = _select_wishlist(state.wishlists, wishlist_id, keywords or [])
        warnings: list[str] = []
        errors: list[str] = []
        run = RadarRun(
            source_ids=[source.id for source in sources],
            wishlist_id=wishlist.id,
            resume_used=bool(resume_text.strip()),
            total_sources=len(sources),
            metadata={
                "limits": {
                    "max_sources": MAX_SOURCES_PER_RUN,
                    "max_results_per_source": MAX_RESULTS_PER_SOURCE,
                    "timeout_seconds": 6,
                },
                "use_ai_requested": use_ai,
            },
        )

        if not sources:
            warnings.append("Nenhuma fonte ativa configurada para o Radar.")
        if not state.wishlists and not keywords:
            warnings.append("Nenhuma wishlist ativa; crie uma wishlist ou informe palavras-chave.")

        inbox_items, _ = self.source_imports.list_imports()
        tracker_items = self.tracker.list_analyses()
        seen_keys = {item.dedupe_key for item in state.results if item.dedupe_key}
        new_results: list[RadarResult] = []
        new_alerts: list[RadarAlert] = []

        for source in sources:
            result = self._collect_source(source)
            source_index = next(
                (i for i, item in enumerate(state.sources) if item.id == source.id), -1
            )
            if source_index >= 0:
                updated_source = source.model_copy(
                    update={
                        "last_checked_at": utc_now(),
                        "last_error": "; ".join(result.failures[:2]),
                        "status": "error" if result.failures else source.status,
                        "updated_at": utc_now(),
                    }
                )
                state.sources[source_index] = updated_source
            if result.failures:
                run.total_errors += len(result.failures)
                errors.extend([f"{source.name}: {failure}" for failure in result.failures])
            for opportunity in result.opportunities[
                : min(source.max_results, MAX_RESULTS_PER_SOURCE)
            ]:
                radar_result = self._result_from_opportunity(
                    opportunity,
                    source=source,
                    run_id=run.id,
                    wishlist=wishlist,
                    resume_text=resume_text,
                    inbox_items=inbox_items,
                    tracker_items=tracker_items,
                )
                if radar_result.dedupe_key in seen_keys:
                    duplicate = next(
                        (
                            item
                            for item in state.results
                            if item.dedupe_key == radar_result.dedupe_key
                        ),
                        None,
                    )
                    radar_result = radar_result.model_copy(
                        update={
                            "radar_status": "duplicate",
                            "duplicate_of": duplicate.id if duplicate else "",
                            "warnings": [
                                *radar_result.warnings,
                                "Resultado duplicado detectado pelo Radar.",
                            ],
                        }
                    )
                    run.total_deduped += 1
                seen_keys.add(radar_result.dedupe_key)
                if use_ai and ai_enricher:
                    radar_result = self._apply_ai_explanation(
                        radar_result,
                        wishlist=wishlist,
                        ai_enricher=ai_enricher,
                    )
                state.results.append(radar_result)
                new_results.append(radar_result)
                run.total_found += 1
                if _should_alert(radar_result, wishlist):
                    alert = RadarAlert(
                        run_id=run.id,
                        result_id=radar_result.id,
                        wishlist_id=wishlist.id,
                        title=f"Nova vaga com {radar_result.radar_score}% de aderencia",
                        message=f"{radar_result.title} em {radar_result.company or radar_result.source_name}",
                        score=radar_result.radar_score,
                        metadata={"source_name": radar_result.source_name},
                    )
                    state.alerts.append(alert)
                    new_alerts.append(alert)
                    run.total_alerted += 1

        run.finished_at = utc_now()
        run.duration_ms = int((time.perf_counter() - started) * 1000)
        run.warnings = warnings
        run.errors = errors
        state.runs.append(run)
        self.store.save(state)
        return run, new_results, new_alerts, warnings

    def list_runs(self) -> list[RadarRun]:
        """List radar run history."""
        return sorted(self.store.load().runs, key=lambda item: item.started_at, reverse=True)

    def list_results(self, *, status: str = "", source_id: str = "") -> list[RadarResult]:
        """List radar results newest first."""
        results = self.store.load().results
        if status:
            results = [item for item in results if item.radar_status == status]
        if source_id:
            results = [item for item in results if item.source_id == source_id]
        return sorted(results, key=lambda item: item.captured_at, reverse=True)

    def update_result(
        self,
        result_id: str,
        *,
        status: RadarResultStatus | None = None,
    ) -> RadarResult:
        """Update one result status."""
        state = self.store.load()
        for index, item in enumerate(state.results):
            if item.id == result_id:
                updates: dict[str, object] = {}
                if status is not None:
                    updates["radar_status"] = status
                updated = item.model_copy(update=updates)
                state.results[index] = updated
                self.store.save(state)
                return updated
        raise KeyError("Resultado do Radar nao encontrado.")

    def save_result_to_inbox(self, result_id: str):
        """Save one radar result to the source inbox for manual review."""
        result = self._get_result(result_id)
        capture = self.source_imports.import_radar_result(
            title=result.title,
            company=result.company,
            text=result.description or result.title,
            url=result.url,
            source_name=f"Radar - {result.source_name}",
            origin=_source_origin_for_radar(result.source_type),
            location=result.location,
            notes=f"Fonte: Radar. Wishlist: {result.wishlist_id or 'busca rapida'}.",
            match_score=result.match_score,
            ats_score=result.ats_score,
            metadata={
                "radar_result_id": result.id,
                "radar_score": result.radar_score,
                "wishlist_id": result.wishlist_id,
                "source_type": result.source_type,
            },
        )
        updated = self.update_result(result_id, status="saved_to_inbox")
        return capture, updated

    def save_result_to_tracker(self, result_id: str) -> tuple[str, RadarResult]:
        """Save one radar result directly to the tracker after user review."""
        result = self._get_result(result_id)
        parsed = parse_job_description(result.description or result.title)
        analysis = JobAnalysisSchema(
            match_score=result.match_score,
            ats_score=result.ats_score,
            opportunity_fit_score=result.wishlist_score,
            risk_score=max(0, 100 - result.radar_score),
            recommendation="apply_with_adjustments"
            if result.radar_score >= 75
            else "save_for_later",
            missing_keywords=result.gaps,
        )
        saved = self.tracker.add_analysis(
            analysis=analysis,
            job_title=result.title,
            company=result.company,
            source_url=result.url,
            collection_method=_collection_method_for_radar(result.source_type),
            requirements=parsed.required_skills,
            notes=(
                f"Fonte: Radar ({result.source_name}). "
                f"Score Radar: {result.radar_score}. Wishlist: {result.wishlist_id}."
            ),
            privacy_acknowledged=True,
            modality=result.work_model,
            seniority=parsed.seniority,
        )
        updated = self.update_result(result_id, status="saved_to_tracker")
        return saved.id, updated

    def list_alerts(self, *, unread_only: bool = False) -> list[RadarAlert]:
        """List local radar alerts."""
        alerts = self.store.load().alerts
        if unread_only:
            alerts = [item for item in alerts if item.status == "unread"]
        return sorted(alerts, key=lambda item: item.created_at, reverse=True)

    def update_alert(
        self,
        alert_id: str,
        *,
        status: RadarAlertStatus | None = None,
    ) -> RadarAlert:
        """Update one alert."""
        state = self.store.load()
        for index, item in enumerate(state.alerts):
            if item.id == alert_id:
                updated = item.model_copy(
                    update={
                        "status": status or item.status,
                        "read_at": utc_now() if status == "read" else item.read_at,
                    }
                )
                state.alerts[index] = updated
                self.store.save(state)
                return updated
        raise KeyError("Alerta do Radar nao encontrado.")

    def stats(self) -> RadarStats:
        """Return compact radar stats."""
        state = self.store.load()
        last_run = max((item.started_at for item in state.runs), default=None)
        return RadarStats(
            active_sources=sum(1 for item in state.sources if item.is_active),
            total_sources=len(state.sources),
            total_results=len(state.results),
            new_results=sum(1 for item in state.results if item.radar_status == "new"),
            matched_results=sum(1 for item in state.results if item.radar_status == "matched"),
            unread_alerts=sum(1 for item in state.alerts if item.status == "unread"),
            duplicates=sum(1 for item in state.results if item.radar_status == "duplicate"),
            source_errors=sum(1 for item in state.sources if item.status == "error"),
            last_run_at=last_run,
        )

    def _collect_source(self, source: RadarSource) -> CollectionResult:
        if source.status in {"disabled", "planned", "requires_official_api", "requires_user_key"}:
            return CollectionResult(
                source=_scraping_source(source),
                failures=[_planned_source_message(source)],
            )
        if source.source_type == "public_feed":
            return RssFeedConnector(self.scraping_client).collect(_scraping_source(source))
        if source.source_type in {"manual_public_page", "manual_url"}:
            return ManualUrlConnector(self.scraping_client).collect(_scraping_source(source))
        if source.source_type == "official_api":
            return CollectionResult(
                source=_scraping_source(source),
                failures=["API oficial cadastrada como estrutura; conector real pendente."],
            )
        return CollectionResult(
            source=_scraping_source(source),
            failures=["Fonte recorrente CSV/JSON fica planejada para uma versao futura."],
        )

    def _result_from_opportunity(
        self,
        opportunity: ScrapedOpportunity,
        *,
        source: RadarSource,
        run_id: str,
        wishlist: JobWishlist,
        resume_text: str,
        inbox_items: Sequence[object],
        tracker_items: Sequence[object],
    ) -> RadarResult:
        description = opportunity.description[:MAX_DESCRIPTION_CHARS]
        normalized = normalize_text(
            " ".join([opportunity.title, opportunity.company or "", description])
        )
        dedupe_key = _dedupe_key(
            opportunity.source_url, opportunity.title, opportunity.company or "", normalized
        )
        match = _score_opportunity(
            title=opportunity.title,
            company=opportunity.company or "",
            description=description,
            location=opportunity.location or "",
            modality=opportunity.modality or "",
            seniority=opportunity.seniority or "",
            wishlist=wishlist,
            resume_text=resume_text,
        )
        already_in_inbox = _already_in_inbox(
            opportunity.source_url,
            opportunity.title,
            opportunity.company or "",
            inbox_items,
        )
        already_in_tracker = _already_in_tracker(
            opportunity.source_url,
            opportunity.title,
            opportunity.company or "",
            tracker_items,
        )
        status: RadarResultStatus = (
            "matched" if match.radar_score >= wishlist.min_match_score else "new"
        )
        warnings = list(match.warnings)
        if already_in_inbox or already_in_tracker:
            status = "duplicate"
            warnings.append("Esta vaga ja aparece na Caixa de Entrada ou no Tracker.")
        return RadarResult(
            run_id=run_id,
            source_id=source.id,
            source_name=source.name,
            source_type=source.source_type,
            wishlist_id=wishlist.id,
            title=opportunity.title or "Vaga sem titulo",
            company=opportunity.company or "",
            url=opportunity.source_url,
            location=opportunity.location or "",
            work_model=opportunity.modality or "",
            employment_type=opportunity.contract_type or "",
            description=description,
            captured_at=opportunity.collected_at,
            normalized_text=normalized,
            dedupe_key=dedupe_key,
            match_score=match.match_score,
            ats_score=match.ats_score,
            wishlist_score=match.wishlist_score,
            radar_score=match.radar_score,
            radar_status=status,
            already_in_inbox=already_in_inbox,
            already_in_tracker=already_in_tracker,
            warnings=warnings,
            reasons=match.reasons,
            evidence=match.evidence,
            gaps=match.gaps,
            next_actions=match.next_actions,
            analysis_mode=match.analysis_mode,
            provider_used=match.provider_used,
            metadata={
                "collection_method": opportunity.collection_method,
                "confidence": opportunity.confidence,
                "tags": opportunity.tags,
                "benefits": opportunity.benefits,
            },
        )

    def _apply_ai_explanation(
        self,
        result: RadarResult,
        *,
        wishlist: JobWishlist,
        ai_enricher: Callable[[RadarResult, JobWishlist], dict[str, object]],
    ) -> RadarResult:
        try:
            output = ai_enricher(result, wishlist)
            return result.model_copy(
                update={
                    "analysis_mode": "ai",
                    "provider_used": str(output.get("provider_used", "gemini")),
                    "reasons": _merge_unique(result.reasons, _list(output.get("match_reasons"))),
                    "evidence": _merge_unique(result.evidence, _list(output.get("evidence"))),
                    "gaps": _merge_unique(result.gaps, _list(output.get("gaps"))),
                    "next_actions": _merge_unique(
                        result.next_actions,
                        _list(output.get("recommended_actions")),
                    ),
                    "warnings": _merge_unique(result.warnings, _list(output.get("warnings"))),
                    "metadata": {
                        **result.metadata,
                        "ai_summary": str(output.get("summary", "")),
                        "ai_confidence": output.get("confidence", 0),
                    },
                }
            )
        except Exception:
            return result.model_copy(
                update={
                    "analysis_mode": "fallback",
                    "provider_used": "local",
                    "warnings": [
                        *result.warnings,
                        "IA falhou no Radar; usei explicacao local.",
                    ],
                }
            )

    def _get_result(self, result_id: str) -> RadarResult:
        for result in self.store.load().results:
            if result.id == result_id:
                return result
        raise KeyError("Resultado do Radar nao encontrado.")


def _select_wishlist(
    wishlists: list[JobWishlist],
    wishlist_id: str,
    keywords: list[str],
) -> JobWishlist:
    if wishlist_id:
        selected = next((item for item in wishlists if item.id == wishlist_id), None)
        if selected is not None:
            return selected
    active = next((item for item in wishlists if item.is_active), None)
    if active is not None:
        return active
    return JobWishlist(
        id="quick-search",
        name="Busca rapida",
        target_titles=keywords,
        required_skills=keywords,
        desired_skills=[],
        min_match_score=70,
        notify_on_new_matches=True,
    )


def _scraping_source(source: RadarSource) -> ScrapingSource:
    mode = (
        "MANUAL_URL"
        if source.source_type in {"manual_public_page", "manual_url"}
        else "PUBLIC_SCRAPING"
    )
    return ScrapingSource(
        name=source.name,
        type=source.source_type,
        url=source.url,
        collection_mode=mode,
        enabled=source.is_active,
        max_items=min(source.max_results, MAX_RESULTS_PER_SOURCE),
        delay_seconds=source.rate_limit_seconds,
        notes=source.notes,
    )


def _default_source_status(
    source_type: RadarSourceType,
    status: RadarSourceStatus,
) -> RadarSourceStatus:
    if source_type == "official_api" and status == "available":
        return "requires_official_api"
    if source_type == "recurring_csv_json" and status == "available":
        return "planned"
    return status


def _planned_source_message(source: RadarSource) -> str:
    if source.source_type == "official_api":
        return "API oficial exige contrato documentado e conector especifico antes de consultar."
    if source.status == "requires_user_key":
        return "Fonte exige chave do usuario; a chave deve ficar apenas no backend local."
    return "Fonte planejada ou desativada; nada foi consultado automaticamente."


def _score_opportunity(
    *,
    title: str,
    company: str,
    description: str,
    location: str,
    modality: str,
    seniority: str,
    wishlist: JobWishlist,
    resume_text: str,
) -> RadarMatch:
    haystack = normalize_text(
        " ".join([title, company, description, location, modality, seniority])
    )
    resume_tokens = _tokens(resume_text)
    score = 10
    reasons: list[str] = []
    evidence: list[str] = []
    gaps: list[str] = []
    warnings: list[str] = []

    title_hit = _first_contained(wishlist.target_titles, haystack)
    if title_hit:
        score += 22
        reasons.append(f"Cargo desejado encontrado: {title_hit}.")
        evidence.append(f"Titulo/fonte cita {title_hit}.")
    elif wishlist.target_titles:
        partial = _token_overlap(wishlist.target_titles, title)
        if partial:
            score += min(12, partial * 4)
            reasons.append("Titulo parcialmente alinhado com os cargos alvo.")
        else:
            gaps.append("Cargo nao bate claramente com a wishlist.")

    required_hits = _matches(wishlist.required_skills, haystack)
    if wishlist.required_skills:
        ratio = len(required_hits) / len(wishlist.required_skills)
        score += round(ratio * 25)
        if required_hits:
            evidence.append(
                "Habilidades obrigatorias encontradas: " + ", ".join(required_hits[:6]) + "."
            )
        missing = [item for item in wishlist.required_skills if item not in required_hits]
        if missing:
            gaps.append("Obrigatorias sem evidencia: " + ", ".join(missing[:6]) + ".")

    desired_hits = _matches(wishlist.desired_skills, haystack)
    if wishlist.desired_skills:
        score += min(15, len(desired_hits) * 4)
        if desired_hits:
            reasons.append("Desejaveis encontrados: " + ", ".join(desired_hits[:6]) + ".")

    domain_hit = _first_contained(wishlist.target_domains + wishlist.industries, haystack)
    if domain_hit:
        score += 8
        reasons.append(f"Dominio alinhado: {domain_hit}.")

    seniority_hit = _first_contained(wishlist.target_seniority, haystack)
    if seniority_hit:
        score += 6
        evidence.append(f"Senioridade compativel: {seniority_hit}.")

    location_hit = _first_contained(wishlist.locations, haystack)
    if location_hit:
        score += 8
        reasons.append(f"Localidade aceita: {location_hit}.")
    if wishlist.remote_preferences and _first_contained(wishlist.remote_preferences, haystack):
        score += 5
        reasons.append("Modelo de trabalho compatível com a preferencia.")

    include_company = _first_contained(wishlist.companies_include, normalize_text(company))
    exclude_company = _first_contained(wishlist.companies_exclude, normalize_text(company))
    if include_company:
        score += 5
        reasons.append("Empresa aparece na lista desejada.")
    if exclude_company:
        score -= 35
        warnings.append("Empresa aparece na lista de exclusao da wishlist.")

    excluded = _first_contained(wishlist.excluded_terms, haystack)
    if excluded:
        score -= 35
        warnings.append(f"Termo excluido encontrado: {excluded}.")

    requirement_tokens = _tokens(" ".join(wishlist.required_skills + wishlist.desired_skills))
    resume_overlap = sorted(requirement_tokens & resume_tokens)
    if resume_overlap:
        score += min(12, len(resume_overlap) * 3)
        evidence.append("Curriculo tem sinais para: " + ", ".join(resume_overlap[:6]) + ".")

    score = max(0, min(100, score))
    match_score = max(0, min(100, score + (4 if resume_text.strip() else 0)))
    ats_score = max(0, min(100, 45 + len(required_hits) * 8 + len(desired_hits) * 4))
    if wishlist.min_ats_score and ats_score < wishlist.min_ats_score:
        gaps.append("ATS estimado abaixo do minimo definido.")

    if not reasons:
        reasons.append("Resultado mantido para revisao manual; sinais ainda sao fracos.")
    if not evidence:
        evidence.append("Evidencias limitadas ao texto publico da fonte.")
    next_actions = [
        "Revisar o texto original antes de salvar.",
        "Enviar para Caixa de Entrada se a vaga fizer sentido.",
        "Rodar compatibilidade com curriculo antes de se candidatar.",
    ]
    return RadarMatch(
        radar_score=score,
        match_score=match_score,
        ats_score=ats_score,
        wishlist_score=score,
        reasons=reasons,
        evidence=evidence,
        gaps=gaps,
        next_actions=next_actions,
        warnings=warnings,
    )


def _dedupe_key(url: str, title: str, company: str, normalized_text: str) -> str:
    normalized_url = normalize_opportunity_url(url)
    if normalized_url:
        return f"url:{normalized_url}"
    key = normalize_text("|".join([company, title]))
    if key.strip("| "):
        return f"title:{hashlib.sha256(key.encode('utf-8')).hexdigest()}"
    return f"text:{hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()}"


def _already_in_inbox(url: str, title: str, company: str, items: Sequence[object]) -> bool:
    current_url = normalize_opportunity_url(url)
    for item in items:
        item_url = normalize_opportunity_url(
            str(getattr(item, "job_url", "") or getattr(item, "source_url", ""))
        )
        if current_url and item_url == current_url:
            return True
        if _same_company_title(
            company, title, getattr(item, "company", ""), getattr(item, "title", "")
        ):
            return True
    return False


def _already_in_tracker(url: str, title: str, company: str, items: Sequence[object]) -> bool:
    current_url = normalize_opportunity_url(url)
    for item in items:
        item_url = normalize_opportunity_url(str(getattr(item, "source", "")))
        if current_url and item_url == current_url:
            return True
        if _same_company_title(
            company, title, getattr(item, "company", ""), getattr(item, "title", "")
        ):
            return True
    return False


def _same_company_title(company_a: str, title_a: str, company_b: str, title_b: str) -> bool:
    if not company_a or not company_b:
        return False
    return normalize_text(company_a) == normalize_text(str(company_b)) and normalize_text(
        title_a
    ) == normalize_text(str(title_b))


def _source_origin_for_radar(source_type: RadarSourceType) -> SourceOrigin:
    if source_type == "public_feed":
        return "public_feed"
    if source_type == "official_api":
        return "official_api_future"
    return "public_source"


def _collection_method_for_radar(source_type: RadarSourceType) -> CollectionMethod:
    if source_type == "public_feed":
        return "rss"
    if source_type == "official_api":
        return "official_api_future"
    return "public_scraping"


def _should_alert(result: RadarResult, wishlist: JobWishlist) -> bool:
    return (
        wishlist.notify_on_new_matches
        and result.radar_status == "matched"
        and result.radar_score >= wishlist.min_match_score
        and result.ats_score >= wishlist.min_ats_score
    )


def _matches(candidates: list[str], haystack: str) -> list[str]:
    return [item for item in candidates if normalize_text(item) in haystack]


def _first_contained(candidates: list[str], haystack: str) -> str:
    return next((item for item in candidates if item and normalize_text(item) in haystack), "")


def _token_overlap(candidates: list[str], text: str) -> int:
    candidate_tokens = _tokens(" ".join(candidates))
    text_tokens = _tokens(text)
    return len(candidate_tokens & text_tokens)


def _tokens(text: str) -> set[str]:
    return {token for token in normalize_text(text).replace("/", " ").split() if len(token) >= 3}


def _merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*primary, *secondary]:
        if item and item not in merged:
            merged.append(item)
    return merged


def _list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []
