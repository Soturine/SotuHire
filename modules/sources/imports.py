"""Local-first source imports, capture history, and opportunity inbox."""

from __future__ import annotations

import csv
import hashlib
import os
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from modules.core.opportunity_identity import normalize_opportunity_url, source_domain
from modules.core.text_utils import normalize_text
from modules.parsers.job_description_parser import parse_job_description
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.schemas.job_posting import JobPostingSchema
from modules.scraping.client import ScrapingClient
from modules.scraping.html_utils import parse_public_html
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker

SourceOrigin = Literal[
    "manual_text",
    "manual_url",
    "csv_import",
    "json_import",
    "extension_capture",
    "companion_capture",
    "public_source",
    "public_feed",
    "official_api_future",
]

CaptureStatus = Literal[
    "new",
    "reviewed",
    "imported_to_job",
    "saved_to_tracker",
    "ignored",
    "archived",
    "duplicate",
    "error",
]

DuplicateDecision = Literal["possible_duplicate", "confirmed_duplicate", "not_duplicate"]
SourceDirectoryKind = Literal[
    "public_career_page",
    "public_feed",
    "official_api",
    "recurring_csv_json",
    "manual_link",
    "observed_origin",
]
SourceDirectoryStatus = Literal["available", "planned", "future", "manual_review"]
SourceExportFormat = Literal["csv", "json"]


def utc_now() -> datetime:
    """Return a timezone-aware timestamp."""
    return datetime.now(UTC)


class JobSource(BaseModel):
    """Configured or observed source for an imported opportunity."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    source_type: SourceOrigin = "manual_text"
    source_name: str = ""
    source_url: str = ""
    origin: SourceOrigin = "manual_text"
    status: str = "active"
    metadata: dict[str, object] = Field(default_factory=dict)


class JobImport(BaseModel):
    """One import event that created or updated an inbox item."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    batch_id: str = ""
    origin: SourceOrigin = "manual_text"
    source_name: str = ""
    source_url: str = ""
    imported_at: datetime = Field(default_factory=utc_now)
    item_id: str = ""
    status: CaptureStatus = "new"
    warnings: list[str] = Field(default_factory=list)


class CaptureRecord(BaseModel):
    """Persistent local record for an imported or captured opportunity."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str = ""
    company: str = ""
    source_type: SourceOrigin = "manual_text"
    source_name: str = ""
    source_url: str = ""
    origin: SourceOrigin = "manual_text"
    captured_at: datetime = Field(default_factory=utc_now)
    imported_at: datetime | None = None
    status: CaptureStatus = "new"
    raw_text: str = ""
    normalized_text: str = ""
    job_url: str = ""
    company_url: str = ""
    location: str = ""
    work_model: str = ""
    employment_type: str = ""
    seniority: str = ""
    domain: str = ""
    tags: list[str] = Field(default_factory=list)
    source_confidence: float = Field(default=0.5, ge=0, le=1)
    dedupe_key: str = ""
    duplicate_of: str = ""
    match_score: int | None = Field(default=None, ge=0, le=100)
    ats_score: int | None = Field(default=None, ge=0, le=100)
    last_analysis_at: datetime | None = None
    notes: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class OpportunityInboxItem(CaptureRecord):
    """UI-facing opportunity inbox item."""


class DuplicateCandidate(BaseModel):
    """Explainable duplicate candidate between two inbox items."""

    model_config = ConfigDict(extra="forbid")

    item_id: str
    duplicate_of: str
    decision: DuplicateDecision = "possible_duplicate"
    reason: str = ""
    confidence: float = Field(default=0.5, ge=0, le=1)


class SourceImportAiContext(BaseModel):
    """Safe optional AI enrichment metadata for source imports."""

    model_config = ConfigDict(extra="forbid")

    requested: bool = False
    provider_used: str = "local"
    requested_provider: str = "local"
    analysis_mode: str = "local"
    model: str = "local"
    tags: list[str] = Field(default_factory=list)
    domain: str = ""
    seniority: str = ""
    priority: str = ""
    summary: str = ""
    duplicate_explanation: str = ""
    inconsistency_alerts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class JobSourceDirectory(BaseModel):
    """Safe source directory card for public/offical source discovery planning."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: SourceDirectoryKind
    status: SourceDirectoryStatus
    base_url: str = ""
    last_checked_at: datetime | None = None
    observation: str = ""
    requires_manual_review: bool = True


class SourceDiscoveryResult(BaseModel):
    """Directory and safe discovery summary."""

    model_config = ConfigDict(extra="forbid")

    sources: list[JobSourceDirectory] = Field(default_factory=list)
    query: str = ""
    warnings: list[str] = Field(default_factory=list)


class SourceExportResult(BaseModel):
    """Local export payload for inbox items."""

    model_config = ConfigDict(extra="forbid")

    format: SourceExportFormat
    filename: str
    content: str
    item_count: int


class ImportBatch(BaseModel):
    """Summary for a CSV, JSON, URL, or text import action."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex)
    origin: SourceOrigin
    source_name: str = ""
    source_url: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    total: int = 0
    imported: int = 0
    errors: int = 0
    duplicates: int = 0
    warnings: list[str] = Field(default_factory=list)
    item_ids: list[str] = Field(default_factory=list)


class SourceImportState(BaseModel):
    """All source import state persisted in one local JSON document."""

    model_config = ConfigDict(extra="forbid")

    sources: list[JobSource] = Field(default_factory=list)
    imports: list[JobImport] = Field(default_factory=list)
    captures: list[CaptureRecord] = Field(default_factory=list)
    batches: list[ImportBatch] = Field(default_factory=list)
    duplicates: list[DuplicateCandidate] = Field(default_factory=list)


class SourceImportStore:
    """Atomic JSON store for local source imports and capture history."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.path = Path(path) if path is not None else base / "sources" / "imports.json"

    def load(self) -> SourceImportState:
        """Read persisted state."""
        if not self.path.exists():
            return SourceImportState()
        try:
            return SourceImportState.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return SourceImportState()

    def save(self, state: SourceImportState) -> SourceImportState:
        """Write state atomically."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return state


class SourceImportService:
    """Application service for imports, inbox actions, and dedupe."""

    def __init__(
        self,
        *,
        store: SourceImportStore | None = None,
        tracker: JobTracker | None = None,
        scraping_client: ScrapingClient | None = None,
    ) -> None:
        self.store = store or SourceImportStore()
        self.tracker = tracker or JobTracker(LocalStore())
        self.scraping_client = scraping_client or ScrapingClient(
            timeout_seconds=6, max_bytes=500_000
        )

    def list_imports(self) -> tuple[list[OpportunityInboxItem], list[ImportBatch]]:
        """Return inbox items and batches from newest to oldest."""
        state = self.store.load()
        captures = sorted(state.captures, key=lambda item: item.captured_at, reverse=True)
        batches = sorted(state.batches, key=lambda item: item.created_at, reverse=True)
        return [
            OpportunityInboxItem.model_validate(item.model_dump()) for item in captures
        ], batches

    def import_text(
        self,
        *,
        text: str,
        url: str = "",
        company: str = "",
        title: str = "",
        source_name: str = "Texto manual",
        notes: str = "",
        use_ai: bool = False,
        ai_context: SourceImportAiContext | None = None,
    ) -> tuple[ImportBatch, list[OpportunityInboxItem], list[str]]:
        """Import a pasted job description."""
        enrichment = ai_context or SourceImportAiContext(requested=use_ai)
        warnings: list[str] = list(enrichment.warnings)
        item = self._item_from_text(
            text,
            origin="manual_text",
            source_name=source_name or "Texto manual",
            source_url=url,
            company_hint=company,
            title_hint=title,
            notes=notes,
            confidence=0.76,
            ai_context=enrichment,
        )
        return self._save_batch("manual_text", [item], source_name=source_name, warnings=warnings)

    def import_url(
        self,
        *,
        url: str,
        source_name: str = "Link manual",
        notes: str = "",
        use_ai: bool = False,
        ai_context: SourceImportAiContext | None = None,
    ) -> tuple[ImportBatch, list[OpportunityInboxItem], list[str]]:
        """Import one public URL when simple reading is allowed."""
        enrichment = ai_context or SourceImportAiContext(requested=use_ai)
        warnings: list[str] = list(enrichment.warnings)
        try:
            fetched = self.scraping_client.fetch(url, delay_seconds=0.2)
            page = parse_public_html(fetched.text, fetched.url)
            text = page.text.strip()
            if not text:
                raise ValueError("A pagina publica nao trouxe texto legivel.")
            item = self._item_from_text(
                text,
                origin="manual_url",
                source_name=source_name or "Link manual",
                source_url=fetched.url,
                title_hint=page.title,
                notes=notes,
                confidence=0.68,
                ai_context=enrichment,
            )
            return self._save_batch(
                "manual_url",
                [item],
                source_name=source_name,
                source_url=fetched.url,
                warnings=warnings,
            )
        except Exception as exc:
            warnings.append(_manual_url_warning(str(exc)))
            item = CaptureRecord(
                title=urlparse(url).netloc or "Link manual",
                source_type="manual_url",
                source_name=source_name or "Link manual",
                source_url=url,
                origin="manual_url",
                status="error",
                job_url=url,
                raw_text="",
                normalized_text="",
                dedupe_key=_dedupe_key("", "", url, ""),
                notes=notes,
                metadata={"error": str(exc)},
            )
            return self._save_batch(
                "manual_url",
                [item],
                source_name=source_name,
                source_url=url,
                warnings=warnings,
            )

    def import_csv(
        self,
        *,
        csv_text: str,
        source_name: str = "CSV Manual",
        use_ai: bool = False,
    ) -> tuple[ImportBatch, list[OpportunityInboxItem], list[str]]:
        """Import rows from CSV text."""
        warnings: list[str] = []
        if use_ai:
            warnings.append("IA em lote usa enriquecimento local nesta versão.")
        reader = csv.DictReader(StringIO(csv_text))
        if not reader.fieldnames:
            raise ValueError("CSV sem cabecalho.")
        items: list[CaptureRecord] = []
        errors = 0
        for row_index, row in enumerate(reader, start=2):
            normalized = _normalize_row(row)
            if not normalized.get("title") and not normalized.get("description"):
                errors += 1
                warnings.append(f"Linha {row_index}: cargo/descricao ausentes.")
                continue
            items.append(
                self._item_from_text(
                    normalized.get("description", ""),
                    origin="csv_import",
                    source_name=normalized.get("source") or source_name,
                    source_url=normalized.get("url", ""),
                    company_hint=normalized.get("company", ""),
                    title_hint=normalized.get("title", ""),
                    location_hint=normalized.get("location", ""),
                    notes=normalized.get("notes", ""),
                    confidence=0.72,
                )
            )
        return self._save_batch(
            "csv_import", items, source_name=source_name, warnings=warnings, errors=errors
        )

    def import_json(
        self,
        *,
        entries: list[dict[str, object]],
        source_name: str = "JSON Manual",
        use_ai: bool = False,
    ) -> tuple[ImportBatch, list[OpportunityInboxItem], list[str]]:
        """Import rows from JSON entries."""
        warnings: list[str] = []
        if use_ai:
            warnings.append("IA em lote usa enriquecimento local nesta versão.")
        items: list[CaptureRecord] = []
        errors = 0
        for index, entry in enumerate(entries, start=1):
            normalized = _normalize_row({key: str(value) for key, value in entry.items()})
            if not normalized.get("title") and not normalized.get("description"):
                errors += 1
                warnings.append(f"Item {index}: cargo/descricao ausentes.")
                continue
            items.append(
                self._item_from_text(
                    normalized.get("description", ""),
                    origin="json_import",
                    source_name=normalized.get("source") or source_name,
                    source_url=normalized.get("url", ""),
                    company_hint=normalized.get("company", ""),
                    title_hint=normalized.get("title", ""),
                    location_hint=normalized.get("location", ""),
                    notes=normalized.get("notes", ""),
                    confidence=0.72,
                )
            )
        return self._save_batch(
            "json_import", items, source_name=source_name, warnings=warnings, errors=errors
        )

    def import_radar_result(
        self,
        *,
        title: str,
        company: str,
        text: str,
        url: str,
        source_name: str,
        origin: SourceOrigin,
        location: str = "",
        notes: str = "",
        match_score: int | None = None,
        ats_score: int | None = None,
        metadata: dict[str, object] | None = None,
    ) -> OpportunityInboxItem:
        """Import one reviewed Radar result into the opportunity inbox."""
        item = self._item_from_text(
            text,
            origin=origin,
            source_name=source_name,
            source_url=url,
            company_hint=company,
            title_hint=title,
            location_hint=location,
            notes=notes,
            confidence=0.78,
        )
        item = item.model_copy(
            update={
                "match_score": match_score,
                "ats_score": ats_score,
                "last_analysis_at": utc_now(),
                "metadata": {
                    **item.metadata,
                    **(metadata or {}),
                    "source_flow": "job_radar",
                },
            }
        )
        _, items, _ = self._save_batch(
            origin,
            [item],
            source_name=source_name,
            source_url=url,
        )
        return items[0]

    def list_captures(self) -> list[OpportunityInboxItem]:
        """Return all local capture records."""
        return self.list_imports()[0]

    def patch_capture(
        self,
        capture_id: str,
        *,
        status: CaptureStatus | None = None,
        notes: str | None = None,
        duplicate_of: str | None = None,
    ) -> OpportunityInboxItem:
        """Update one capture status or notes."""
        state = self.store.load()
        for index, item in enumerate(state.captures):
            if item.id == capture_id:
                updates: dict[str, object] = {}
                if status is not None:
                    updates["status"] = status
                if notes is not None:
                    updates["notes"] = notes
                if duplicate_of is not None:
                    updates["duplicate_of"] = duplicate_of
                updated = item.model_copy(update=updates)
                state.captures[index] = updated
                self.store.save(state)
                return OpportunityInboxItem.model_validate(updated.model_dump())
        raise KeyError("Captura nao encontrada.")

    def merge_duplicate(
        self,
        capture_id: str,
        *,
        duplicate_of: str,
        notes: str = "",
    ) -> OpportunityInboxItem:
        """Mark one duplicate as merged while preserving both source records."""
        state = self.store.load()
        existing = next((item for item in state.captures if item.id == duplicate_of), None)
        if existing is None:
            raise KeyError("Captura existente nao encontrada.")

        for index, item in enumerate(state.captures):
            if item.id == capture_id:
                merged_at = utc_now().isoformat()
                metadata = {
                    **item.metadata,
                    "merge_action": "merged_into_existing",
                    "merged_at": merged_at,
                    "merged_into": duplicate_of,
                    "existing_source": existing.source_name,
                }
                merge_note = (
                    notes or f"Mesclada com {existing.title or duplicate_of}; historico preservado."
                )
                updated = item.model_copy(
                    update={
                        "status": "archived",
                        "duplicate_of": duplicate_of,
                        "notes": _merge_notes(item.notes, merge_note),
                        "metadata": metadata,
                    }
                )
                state.captures[index] = updated
                state.duplicates.append(
                    DuplicateCandidate(
                        item_id=item.id,
                        duplicate_of=duplicate_of,
                        decision="confirmed_duplicate",
                        reason="Mescla visual confirmada pelo usuário; histórico preservado.",
                        confidence=0.95,
                    )
                )
                self.store.save(state)
                return OpportunityInboxItem.model_validate(updated.model_dump())
        raise KeyError("Captura nao encontrada.")

    def import_capture_to_job(
        self, capture_id: str
    ) -> tuple[OpportunityInboxItem, JobPostingSchema]:
        """Return a parsed job from a capture and mark it as imported."""
        item = self.patch_capture(capture_id, status="imported_to_job")
        job = parse_job_description(item.raw_text or item.title).model_copy(
            update={
                "title": item.title,
                "company": item.company,
                "location": item.location,
                "raw_text": "",
            }
        )
        return item, job

    def save_capture_to_tracker(self, capture_id: str) -> tuple[OpportunityInboxItem, str]:
        """Save one inbox item into the local application tracker."""
        item = self._get_capture(capture_id)
        parsed = parse_job_description(item.raw_text or item.title)
        analysis = JobAnalysisSchema(
            match_score=item.match_score or 0,
            ats_score=item.ats_score or 0,
            opportunity_fit_score=0,
            risk_score=0,
            recommendation="save_for_later",
        )
        saved = self.tracker.add_analysis(
            analysis=analysis,
            job_title=item.title,
            company=item.company,
            source_url=item.job_url or item.source_url,
            collection_method=_collection_method(item.origin),
            requirements=parsed.required_skills,
            notes=item.notes or f"Fonte: {source_label(item.origin)}",
            privacy_acknowledged=True,
            modality=item.work_model,
            seniority=item.seniority,
        )
        updated = self.patch_capture(
            capture_id,
            status="saved_to_tracker",
            notes=item.notes or f"Salva em Candidaturas como {saved.id}.",
        )
        return updated, saved.id

    def dedupe(self) -> list[DuplicateCandidate]:
        """Recalculate duplicate candidates and persist duplicate markers."""
        state = self.store.load()
        duplicates = _find_duplicates(state.captures)
        for duplicate in duplicates:
            for index, item in enumerate(state.captures):
                if item.id == duplicate.item_id and item.status not in {"archived", "ignored"}:
                    state.captures[index] = item.model_copy(
                        update={"status": "duplicate", "duplicate_of": duplicate.duplicate_of}
                    )
        state.duplicates = duplicates
        self.store.save(state)
        return duplicates

    def source_directory(self, query: str = "") -> SourceDiscoveryResult:
        """Return safe source directory entries without running broad scraping."""
        state = self.store.load()
        sources = _default_source_directory()
        observed: dict[str, JobSourceDirectory] = {}
        for item in state.captures:
            key = item.domain or source_label(item.origin)
            if not key:
                continue
            observed[key] = JobSourceDirectory(
                id=f"observed-{normalize_text(key).replace(' ', '-')}",
                name=f"Fonte observada: {key}",
                kind="observed_origin",
                status="available",
                base_url=item.source_url or item.job_url,
                last_checked_at=item.captured_at,
                observation=f"Origem local: {source_label(item.origin)}.",
                requires_manual_review=True,
            )
        sources.extend(observed.values())
        cleaned_query = normalize_text(query)
        if cleaned_query:
            sources = [
                source
                for source in sources
                if cleaned_query
                in normalize_text(
                    " ".join([source.name, source.kind, source.status, source.observation])
                )
            ]
        return SourceDiscoveryResult(
            sources=sources,
            query=query,
            warnings=[
                "Diretório seguro: não faz login automático, bypass de CAPTCHA ou candidatura automática."
            ],
        )

    def export_items(
        self,
        *,
        export_format: SourceExportFormat,
        item_ids: list[str] | None = None,
    ) -> SourceExportResult:
        """Export inbox items to local CSV or JSON content."""
        state = self.store.load()
        wanted = set(item_ids or [])
        items = [item for item in state.captures if not wanted or item.id in wanted]
        exported = [_export_row(item) for item in items]
        timestamp = utc_now().strftime("%Y%m%d-%H%M%S")
        if export_format == "json":
            import json

            return SourceExportResult(
                format="json",
                filename=f"sotuhire-opportunities-{timestamp}.json",
                content=json.dumps(exported, ensure_ascii=False, indent=2),
                item_count=len(exported),
            )

        stream = StringIO()
        fieldnames = [
            "cargo",
            "empresa",
            "link",
            "origem",
            "status",
            "data",
            "score",
            "ats_score",
            "tags",
            "notas",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(exported)
        return SourceExportResult(
            format="csv",
            filename=f"sotuhire-opportunities-{timestamp}.csv",
            content=stream.getvalue(),
            item_count=len(exported),
        )

    def stats(self) -> dict[str, int | dict[str, int]]:
        """Return compact inbox stats."""
        state = self.store.load()
        by_status: dict[str, int] = {}
        by_origin: dict[str, int] = {}
        for item in state.captures:
            by_status[item.status] = by_status.get(item.status, 0) + 1
            by_origin[item.origin] = by_origin.get(item.origin, 0) + 1
        return {
            "total": len(state.captures),
            "duplicates": sum(1 for item in state.captures if item.status == "duplicate"),
            "errors": sum(1 for item in state.captures if item.status == "error"),
            "saved_to_tracker": sum(
                1 for item in state.captures if item.status == "saved_to_tracker"
            ),
            "by_status": by_status,
            "by_origin": by_origin,
        }

    def _save_batch(
        self,
        origin: SourceOrigin,
        items: list[CaptureRecord],
        *,
        source_name: str = "",
        source_url: str = "",
        warnings: list[str] | None = None,
        errors: int = 0,
    ) -> tuple[ImportBatch, list[OpportunityInboxItem], list[str]]:
        state = self.store.load()
        batch = ImportBatch(
            origin=origin,
            source_name=source_name,
            source_url=source_url,
            total=len(items) + errors,
            errors=errors,
            warnings=warnings or [],
        )
        saved: list[CaptureRecord] = []
        duplicate_count = 0
        for item in items:
            duplicate = _first_duplicate(item, state.captures)
            if duplicate:
                duplicate_count += 1
                item = item.model_copy(update={"status": "duplicate", "duplicate_of": duplicate.id})
                state.duplicates.append(
                    DuplicateCandidate(
                        item_id=item.id,
                        duplicate_of=duplicate.id,
                        reason=_duplicate_reason(item, duplicate),
                        confidence=0.92 if normalize_opportunity_url(item.job_url) else 0.78,
                    )
                )
            state.captures.append(item)
            state.imports.append(
                JobImport(
                    batch_id=batch.id,
                    origin=origin,
                    source_name=item.source_name,
                    source_url=item.source_url or item.job_url,
                    item_id=item.id,
                    status=item.status,
                    warnings=batch.warnings,
                )
            )
            batch.item_ids.append(item.id)
            saved.append(item)
        batch.imported = len(saved)
        batch.duplicates = duplicate_count
        state.batches.append(batch)
        self.store.save(state)
        return (
            batch,
            [OpportunityInboxItem.model_validate(item.model_dump()) for item in saved],
            batch.warnings,
        )

    def _item_from_text(
        self,
        text: str,
        *,
        origin: SourceOrigin,
        source_name: str,
        source_url: str = "",
        company_hint: str = "",
        title_hint: str = "",
        location_hint: str = "",
        notes: str = "",
        confidence: float = 0.65,
        ai_context: SourceImportAiContext | None = None,
    ) -> CaptureRecord:
        parsed = parse_job_description(text or title_hint)
        title = title_hint or parsed.title or "Vaga sem titulo"
        company = company_hint or parsed.company or ""
        normalized = normalize_text(text)
        enrichment = ai_context or SourceImportAiContext()
        tags = _unique([*parsed.ats_keywords[:10], *parsed.required_skills[:8], *enrichment.tags])
        metadata = _source_import_metadata(text, parsed, enrichment)
        return CaptureRecord(
            title=title,
            company=company,
            source_type=origin,
            source_name=source_name,
            source_url=source_url,
            origin=origin,
            imported_at=utc_now(),
            raw_text=text.strip(),
            normalized_text=normalized,
            job_url=source_url,
            location=location_hint or parsed.location,
            work_model="" if parsed.modality == "unknown" else parsed.modality,
            employment_type=parsed.contract,
            seniority=enrichment.seniority or parsed.seniority,
            domain=enrichment.domain or (source_domain(source_url) if source_url else ""),
            tags=tags,
            source_confidence=confidence,
            dedupe_key=_dedupe_key(title, company, source_url, normalized),
            notes=notes,
            metadata=metadata,
        )

    def _get_capture(self, capture_id: str) -> CaptureRecord:
        for item in self.store.load().captures:
            if item.id == capture_id:
                return item
        raise KeyError("Captura nao encontrada.")


def source_label(origin: str) -> str:
    """Return a UI label for one source origin."""
    labels = {
        "manual_text": "Texto manual",
        "manual_url": "Link manual",
        "csv_import": "CSV",
        "json_import": "JSON",
        "extension_capture": "Extensao Local",
        "companion_capture": "Companion",
        "public_source": "Fonte publica",
        "public_feed": "Feed publico",
        "official_api_future": "API oficial futura",
    }
    return labels.get(origin, origin)


def _collection_method(origin: SourceOrigin):
    if origin == "manual_text":
        return "manual_text"
    if origin == "csv_import":
        return "csv_import"
    if origin == "json_import":
        return "json_import"
    if origin in {"extension_capture", "companion_capture"}:
        return "browser_assisted_capture"
    if origin in {"public_source", "public_feed"}:
        return "public_scraping"
    return "manual_url"


def _normalize_row(row: dict[str, str]) -> dict[str, str]:
    aliases = {
        "cargo": "title",
        "title": "title",
        "empresa": "company",
        "company": "company",
        "link": "url",
        "url": "url",
        "local": "location",
        "location": "location",
        "descricao": "description",
        "descrição": "description",
        "description": "description",
        "fonte": "source",
        "source": "source",
        "status": "status",
        "observacoes": "notes",
        "observações": "notes",
        "notes": "notes",
    }
    normalized: dict[str, str] = {}
    for key, value in row.items():
        canonical = aliases.get(normalize_text(str(key)).replace(" ", "_"), "")
        if canonical:
            normalized[canonical] = str(value or "").strip()
    return normalized


def _first_duplicate(item: CaptureRecord, existing: list[CaptureRecord]) -> CaptureRecord | None:
    for current in existing:
        if current.status in {"archived", "ignored"}:
            continue
        if normalize_opportunity_url(item.job_url) and normalize_opportunity_url(
            item.job_url
        ) == normalize_opportunity_url(current.job_url):
            return current
        if item.company and current.company:
            company_match = normalize_text(item.company) == normalize_text(current.company)
            title_match = _title_similarity(item.title, current.title) >= 0.72
            location_match = (
                not item.location
                or not current.location
                or normalize_text(item.location) == normalize_text(current.location)
            )
            if company_match and title_match and location_match:
                return current
        if (
            item.normalized_text
            and current.normalized_text
            and _text_hash(item.normalized_text) == _text_hash(current.normalized_text)
        ):
            return current
    return None


def _find_duplicates(items: list[CaptureRecord]) -> list[DuplicateCandidate]:
    duplicates: list[DuplicateCandidate] = []
    seen: list[CaptureRecord] = []
    for item in sorted(items, key=lambda value: value.captured_at):
        duplicate = _first_duplicate(item, seen)
        if duplicate:
            duplicates.append(
                DuplicateCandidate(
                    item_id=item.id,
                    duplicate_of=duplicate.id,
                    reason=_duplicate_reason(item, duplicate),
                    confidence=0.92 if normalize_opportunity_url(item.job_url) else 0.78,
                )
            )
        seen.append(item)
    return duplicates


def _duplicate_reason(item: CaptureRecord, duplicate: CaptureRecord) -> str:
    if normalize_opportunity_url(item.job_url) and normalize_opportunity_url(
        item.job_url
    ) == normalize_opportunity_url(duplicate.job_url):
        return "URL normalizada igual."
    if normalize_text(item.company) == normalize_text(duplicate.company):
        return "Empresa e cargo muito parecidos."
    return "Descricao normalizada muito semelhante."


def _dedupe_key(title: str, company: str, url: str, normalized_text: str) -> str:
    normalized_url = normalize_opportunity_url(url)
    if normalized_url:
        return f"url:{normalized_url}"
    if title or company:
        return f"job:{normalize_text(company)}|{normalize_text(title)}"
    return f"text:{_text_hash(normalized_text)}"


def _text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _title_similarity(left: str, right: str) -> float:
    left_tokens = set(normalize_text(left).split())
    right_tokens = set(normalize_text(right).split())
    if not left_tokens or not right_tokens:
        return 0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _manual_url_warning(error: str) -> str:
    return (
        "A pagina nao pode ser lida automaticamente. Se ela exigir login, bloquear acesso "
        "ou nao permitir leitura publica simples, faca login manualmente no navegador autorizado "
        "ou cole o texto da vaga manualmente. Detalhe local: "
        f"{error}"
    )


def _source_import_metadata(
    text: str,
    parsed: JobPostingSchema,
    enrichment: SourceImportAiContext,
) -> dict[str, object]:
    summary = enrichment.summary or _local_summary(text, parsed)
    priority = enrichment.priority or _local_priority(parsed)
    metadata: dict[str, object] = {
        "analysis_mode": enrichment.analysis_mode,
        "provider_used": enrichment.provider_used,
        "requested_provider": enrichment.requested_provider,
        "model": enrichment.model,
        "summary": summary,
        "priority": priority,
        "facts_only": True,
        "inferences": {
            "domain": enrichment.domain,
            "seniority": enrichment.seniority,
            "tags": enrichment.tags,
        },
        "inconsistency_alerts": enrichment.inconsistency_alerts,
    }
    if enrichment.duplicate_explanation:
        metadata["duplicate_explanation"] = enrichment.duplicate_explanation
    return metadata


def _local_summary(text: str, parsed: JobPostingSchema) -> str:
    if parsed.title or parsed.company:
        parts = [part for part in [parsed.title, parsed.company, parsed.location] if part]
        return " · ".join(parts)
    compact = " ".join(text.split())
    return compact[:180]


def _local_priority(parsed: JobPostingSchema) -> str:
    signals = [
        bool(parsed.required_skills),
        bool(parsed.ats_keywords),
        bool(parsed.title),
        bool(parsed.company),
        parsed.modality != "unknown",
    ]
    score = sum(signals)
    if score >= 4:
        return "alta"
    if score >= 2:
        return "media"
    return "baixa"


def _merge_notes(existing: str, note: str) -> str:
    if existing and note:
        return f"{existing}\n{note}"
    return existing or note


def _export_row(item: CaptureRecord) -> dict[str, str]:
    return {
        "cargo": item.title,
        "empresa": item.company,
        "link": item.job_url or item.source_url,
        "origem": source_label(item.origin),
        "status": item.status,
        "data": (item.imported_at or item.captured_at).isoformat(),
        "score": "" if item.match_score is None else str(item.match_score),
        "ats_score": "" if item.ats_score is None else str(item.ats_score),
        "tags": ", ".join(item.tags),
        "notas": item.notes,
    }


def _default_source_directory() -> list[JobSourceDirectory]:
    return [
        JobSourceDirectory(
            id="open-career-pages",
            name="Páginas de carreira abertas",
            kind="public_career_page",
            status="planned",
            observation="Leitura pública simples futura, sempre com revisão manual.",
        ),
        JobSourceDirectory(
            id="public-rss-feeds",
            name="Feeds RSS públicos",
            kind="public_feed",
            status="available",
            observation="RSS/Atom publico com refresh manual pelo Radar, sem salvar no tracker sem acao.",
        ),
        JobSourceDirectory(
            id="official-apis",
            name="APIs oficiais",
            kind="official_api",
            status="planned",
            observation="Somente APIs documentadas, com chave do usuario quando aplicavel.",
        ),
        JobSourceDirectory(
            id="recurring-csv-json",
            name="CSV/JSON recorrente",
            kind="recurring_csv_json",
            status="available",
            observation="Importação manual recorrente com revisão antes de analisar ou salvar.",
        ),
        JobSourceDirectory(
            id="manual-links",
            name="Links manuais",
            kind="manual_link",
            status="available",
            observation="Links adicionados pelo usuário e registrados no histórico local.",
        ),
    ]


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))
