"""Dependency-free application service for browser-assisted job captures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast

from pydantic import ValidationError

from modules.ai.structured_analysis import analyze_structured, get_provider
from modules.context import (
    CareerContextEngine,
    CareerContextPurpose,
    context_brief,
    format_context_for_prompt,
)
from modules.core.opportunity_identity import (
    opportunity_identity_hash,
    same_opportunity,
    source_domain,
)
from modules.github_analyzer import analyze_github_repository, project_report_from_github_analysis
from modules.github_analyzer.exceptions import GitHubAnalyzerError
from modules.local_api.compatibility import APP_VERSION, compatible_extension
from modules.local_api.schemas import (
    ApplicationBatchPayload,
    BrowserCapturePayload,
    CaptureActionRequest,
    CompanionAnalysisContext,
    CompanionCaptureRecord,
    CompanionContextSummaryResponse,
    CompanionHandshakeRequest,
    CompanionHandshakeResponse,
    CompanionResponse,
    ProjectCompanionResponse,
    utc_now,
)
from modules.local_api.security import (
    configured_token,
    is_local_client,
    sanitize_text,
    token_is_valid,
)
from modules.memory import CareerMemory
from modules.opportunities import OpportunityStore
from modules.parsers.job_description_parser import parse_job_description
from modules.portfolio import (
    ProjectAnalysisPayload,
    ProjectAnalysisRecord,
    ProjectAnalysisReport,
    ProjectAnalysisStore,
    analyze_project,
    enhance_project_report,
)
from modules.schemas.job_analysis import JobAnalysisSchema, Recommendation
from modules.schemas.user_preferences import UserPreferences
from modules.scraping.connectors.manual_url import opportunity_from_text
from modules.storage import (
    AnalysisSnapshot,
    JobSnapshot,
    PublicExamSnapshot,
    ResumeSnapshot,
    SnapshotStore,
)
from modules.storage.local_store import LocalStore
from modules.tracker.job_tracker import JobTracker


def sanitize_capture(payload: BrowserCapturePayload) -> BrowserCapturePayload:
    """Sanitize only user-visible text while preserving typed metadata."""
    return payload.model_copy(
        update={
            "page_title": sanitize_text(payload.page_title, limit=500),
            "domain": sanitize_text(payload.domain, limit=255),
            "visible_text": sanitize_text(payload.visible_text, limit=200_000),
            "job_title": sanitize_text(payload.job_title, limit=500),
            "company": sanitize_text(payload.company, limit=500),
            "location": sanitize_text(payload.location, limit=500),
            "description": sanitize_text(payload.description, limit=100_000),
            "extraction_strategy": sanitize_text(payload.extraction_strategy, limit=80),
            "structured_data": _safe_structured_data(payload.structured_data),
        }
    )


def _safe_structured_data(payload: dict[str, object]) -> dict[str, object]:
    """Keep only bounded public JobPosting fields from page JSON-LD."""
    allowed = {
        "@context",
        "@type",
        "title",
        "description",
        "datePosted",
        "validThrough",
        "employmentType",
        "hiringOrganization",
        "jobLocation",
        "jobLocationType",
        "applicantLocationRequirements",
        "baseSalary",
        "identifier",
        "url",
    }
    result: dict[str, object] = {}
    for key, value in payload.items():
        if key not in allowed:
            continue
        if isinstance(value, str):
            result[key] = sanitize_text(value, limit=20_000)
        elif isinstance(value, (bool, int, float)) or value is None:
            result[key] = value
        elif isinstance(value, (dict, list)):
            encoded = json.dumps(value, ensure_ascii=False, default=str)
            if len(encoded) <= 30_000:
                result[key] = value
    return result


class CompanionCaptureStore:
    """Small atomic JSONL store for browser captures."""

    def __init__(self, path: str | Path | None = None) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.path = Path(path) if path is not None else base / "companion" / "captures.jsonl"

    def list(self) -> list[CompanionCaptureRecord]:
        if not self.path.exists():
            return []
        try:
            records = [
                CompanionCaptureRecord.model_validate_json(line)
                for line in self.path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, ValueError):
            return []
        return sorted(records, key=lambda record: record.updated_at, reverse=True)

    def get(self, capture_id: str) -> CompanionCaptureRecord | None:
        return next((record for record in self.list() if record.id == capture_id), None)

    def save(self, record: CompanionCaptureRecord) -> CompanionCaptureRecord:
        records = self.list()
        record = record.model_copy(update={"updated_at": utc_now()})
        for index, current in enumerate(records):
            if current.id == record.id:
                records[index] = record
                break
        else:
            records.append(record)
        self._write(records)
        return record

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

    def _write(self, records: list[CompanionCaptureRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            "\n".join(record.model_dump_json() for record in records) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)


class LocalCompanionService:
    """Capture, analyze, and track browser-assisted opportunities locally."""

    def __init__(
        self,
        *,
        capture_store: CompanionCaptureStore | None = None,
        opportunity_store: OpportunityStore | None = None,
        memory: CareerMemory | None = None,
        tracker: JobTracker | None = None,
        context_path: str | Path | None = None,
        project_store: ProjectAnalysisStore | None = None,
    ) -> None:
        base = Path(os.getenv("SOTUHIRE_DATA_DIR", "data"))
        self.capture_store = capture_store or CompanionCaptureStore()
        self.opportunity_store = opportunity_store or OpportunityStore(
            base / "sotuhire-opportunities.json"
        )
        self.memory = memory or CareerMemory()
        self.tracker = tracker or JobTracker(LocalStore(base / "sotuhire-history.json"))
        self.context_path = (
            Path(context_path)
            if context_path is not None
            else base / "companion" / "active-context.json"
        )
        self.project_store = project_store or ProjectAnalysisStore(
            base / "portfolio" / "project-analyses.jsonl"
        )
        self.snapshots = SnapshotStore(base / "sotuhire.db")

    def health(self) -> CompanionResponse:
        return CompanionResponse(message="SotuHire Local Companion disponível.")

    def handshake(self, request: CompanionHandshakeRequest) -> CompanionHandshakeResponse:
        """Negotiate extension/companion capabilities without exchanging secrets."""
        compatible, warnings = compatible_extension(request.extension_version)
        return CompanionHandshakeResponse(
            extension_version=request.extension_version,
            compatible=compatible,
            warnings=warnings,
        )

    def context_summary(self) -> CompanionContextSummaryResponse:
        """Return a short, non-sensitive context summary for the extension popup."""
        context = self._load_context()
        career_context = CareerContextEngine().build(
            CareerContextPurpose.EXTENSION,
            query="extensão local companion",
            max_evidence=8,
        )
        records = self.capture_store.list()
        provider = (context.provider or "local").strip().lower()
        public_exam_count = sum(1 for record in records if record.capture.kind == "public_exam")
        safe_summary = context_brief(career_context)
        profile_available = bool(context.resume_text.strip() or safe_summary)
        return CompanionContextSummaryResponse(
            app_version=os.getenv("SOTUHIRE_APP_VERSION", APP_VERSION),
            profile_available=profile_available,
            profile_summary=(
                safe_summary or "Resumo seguro disponível no backend local."
                if profile_available
                else "Perfil local ainda sem resumo seguro ativo."
            ),
            enabled_flows=["job", "public_exam", "github", "profile_evidence"],
            ai_provider_status="configured" if provider not in {"", "local"} else "local",
            warnings=(
                [
                    *career_context.warnings,
                    f"{public_exam_count} captura(s) de edital/concurso aguardam revisão.",
                ]
                if public_exam_count
                else career_context.warnings
            ),
        )

    def save_active_context(self, context: CompanionAnalysisContext) -> Path:
        self.context_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.context_path.with_suffix(".tmp")
        temporary.write_text(context.model_dump_json(), encoding="utf-8")
        temporary.replace(self.context_path)
        return self.context_path

    def capture_job(self, payload: BrowserCapturePayload) -> CompanionResponse:
        clean = sanitize_capture(payload)
        capture_id = opportunity_identity_hash(
            clean.job_title or clean.page_title,
            clean.company,
            clean.url,
        )
        current = next(
            (
                record
                for record in self.capture_store.list()
                if same_opportunity(
                    left_title=record.capture.job_title or record.capture.page_title,
                    left_company=record.capture.company,
                    left_urls=record.source_urls or [record.capture.url],
                    right_title=clean.job_title or clean.page_title,
                    right_company=clean.company,
                    right_url=clean.url,
                )
            ),
            None,
        )
        if current is not None:
            capture_id = current.id
        text = clean.description or clean.visible_text
        snapshot = self.snapshots.create_job(
            JobSnapshot(
                opportunity_id=capture_id,
                title=clean.job_title or clean.page_title,
                organization=clean.company,
                location=clean.location,
                description=text,
                source_url=clean.url,
                source_refs=list(
                    dict.fromkeys([*(current.source_urls if current else []), clean.url])
                ),
                source_kind=clean.collection_method,
                raw_text=text,
                structured_data=clean.model_dump(mode="json"),
                captured_at=clean.captured_at,
            )
        )
        record = self.capture_store.save(
            (
                current
                or CompanionCaptureRecord(
                    id=capture_id,
                    capture=clean,
                    source_urls=[clean.url],
                    source_domains=[source_domain(clean.url)],
                )
            ).model_copy(
                update={
                    "capture": clean,
                    "source_urls": list(
                        dict.fromkeys([*(current.source_urls if current else []), clean.url])
                    ),
                    "source_domains": list(
                        dict.fromkeys(
                            [
                                *(current.source_domains if current else []),
                                source_domain(clean.url),
                            ]
                        )
                    ),
                    "snapshot_id": snapshot.snapshot_id,
                    "snapshot_history": list(
                        dict.fromkeys(
                            [*(current.snapshot_history if current else []), snapshot.snapshot_id]
                        )
                    ),
                    "content_hash": snapshot.content_hash,
                }
            )
        )
        opportunity = opportunity_from_text(
            text,
            source="Extensão assistiva SotuHire",
            source_url=clean.url,
            collection_method="browser_assisted_capture",
        ).model_copy(
            update={
                "title": clean.job_title or clean.page_title,
                "company": clean.company or None,
                "location": clean.location or None,
                "confidence": 0.8,
            }
        )
        self.opportunity_store.save_many([opportunity])
        self.memory.remember_opportunity(
            title=clean.job_title or clean.page_title,
            company=clean.company,
            source="browser_assisted_capture",
            source_id=record.id,
            details=text,
            tags=["browser_assisted_capture", clean.domain],
        )
        return CompanionResponse(
            message="Vaga capturada localmente.",
            capture_id=record.id,
            snapshot_id=snapshot.snapshot_id,
        )

    def capture_public_exam(self, payload: BrowserCapturePayload) -> CompanionResponse:
        """Save a visible edital/concurso page without treating it as a private job."""
        clean = sanitize_capture(payload).model_copy(update={"kind": "public_exam"})
        capture_id = opportunity_identity_hash(
            clean.page_title or "edital-concurso",
            "public_exam",
            clean.url,
        )
        current = next(
            (
                record
                for record in self.capture_store.list()
                if record.capture.kind == "public_exam" and clean.url in record.source_urls
            ),
            None,
        )
        if current is not None:
            capture_id = current.id
        text = clean.description or clean.visible_text
        snapshot = self.snapshots.create_public_exam(
            PublicExamSnapshot(
                notice_id=capture_id,
                raw_text=text,
                structured_notice=clean.model_dump(mode="json"),
                captured_at=clean.captured_at,
            )
        )
        record = self.capture_store.save(
            (
                current
                or CompanionCaptureRecord(
                    id=capture_id,
                    capture=clean,
                    source_urls=[clean.url],
                    source_domains=[source_domain(clean.url)],
                )
            ).model_copy(
                update={
                    "capture": clean,
                    "source_urls": list(
                        dict.fromkeys([*(current.source_urls if current else []), clean.url])
                    ),
                    "source_domains": list(
                        dict.fromkeys(
                            [
                                *(current.source_domains if current else []),
                                source_domain(clean.url),
                            ]
                        )
                    ),
                    "snapshot_id": snapshot.snapshot_id,
                    "snapshot_history": list(
                        dict.fromkeys(
                            [*(current.snapshot_history if current else []), snapshot.snapshot_id]
                        )
                    ),
                    "content_hash": snapshot.content_hash,
                }
            )
        )
        return CompanionResponse(
            message="Edital/concurso capturado localmente para revisao.",
            capture_id=record.id,
            snapshot_id=snapshot.snapshot_id,
        )

    def analyze_capture(self, request: CaptureActionRequest) -> CompanionResponse:
        record = self._resolve_record(request)
        context = self._load_context()
        career_context = CareerContextEngine().build(
            CareerContextPurpose.EXTENSION,
            query=record.capture.description or record.capture.visible_text,
            max_evidence=8,
        )
        safe_profile_text = format_context_for_prompt(
            career_context,
            include_sensitive=False,
            confirmed_only=True,
        )
        resume_text = context.resume_text or safe_profile_text
        job_text = record.capture.description or record.capture.visible_text
        evidence = self.memory.retriever.retrieve(job_text, top_k=6)
        result = analyze_structured(
            resume_text,
            job_text,
            UserPreferences.model_validate(context.preferences),
            provider=get_provider(context.provider if request.use_ai else "local"),
            memory_evidence=evidence,
        )
        job = parse_job_description(job_text)
        self.memory.remember_analysis(
            result.analysis,
            job_title=record.capture.job_title or job.title,
            company=record.capture.company or job.company,
            source_id=record.id,
        )
        summary = {
            "match_score": result.analysis.match_score,
            "ats_score": result.analysis.ats_score,
            "recommendation": result.analysis.recommendation,
            "provider": result.provider,
            "fallback_used": result.fallback_used,
        }
        resume_snapshot_id = ""
        if resume_text.strip():
            resume_snapshot_id = self.snapshots.create_resume(
                ResumeSnapshot(
                    profile_id="default",
                    resume_variant_id="extension-context",
                    title="Contexto usado pela extensão",
                    content=resume_text,
                )
            ).snapshot_id
        analysis_snapshot = self.snapshots.create_analysis(
            AnalysisSnapshot(
                analysis_type="extension_match",
                job_snapshot_id=record.snapshot_id,
                resume_snapshot_id=resume_snapshot_id,
                provider_requested=context.provider if request.use_ai else "local",
                provider_used=result.provider,
                model_requested=getattr(result, "model", "local"),
                model_used=getattr(result, "model", "local"),
                prompt_id="match_analysis_evidence_based_v1",
                prompt_version="1.0.0",
                fallback_used=result.fallback_used,
                result=result.analysis.model_dump(mode="json"),
                evidence_used=[item.model_dump(mode="json") for item in evidence],
                source_refs=record.source_urls,
            )
        )
        self.capture_store.save(
            record.model_copy(
                update={
                    "status": "analyzed",
                    "analysis_summary": summary,
                    "analysis_snapshot_id": analysis_snapshot.snapshot_id,
                }
            )
        )
        return CompanionResponse(
            message="Vaga analisada localmente.",
            capture_id=record.id,
            match_score=result.analysis.match_score,
            ats_score=result.analysis.ats_score,
            recommendation=result.analysis.recommendation,
            provider=result.provider,
            snapshot_id=record.snapshot_id,
        )

    def track_capture(self, request: CaptureActionRequest) -> CompanionResponse:
        analysis_response = self.analyze_capture(request)
        record = self.capture_store.get(analysis_response.capture_id)
        if record is None:
            raise KeyError("Captura não encontrada após análise.")
        summary = record.analysis_summary
        analysis = JobAnalysisSchema(
            match_score=_summary_int(summary, "match_score"),
            ats_score=_summary_int(summary, "ats_score"),
            opportunity_fit_score=0,
            risk_score=0,
            recommendation=cast(
                Recommendation, str(summary.get("recommendation", "save_for_later"))
            ),
        )
        tracked = self.tracker.add_analysis(
            analysis,
            job_title=record.capture.job_title or record.capture.page_title,
            company=record.capture.company,
            notes=f"Capturada pela extensão: {record.capture.url}",
            privacy_acknowledged=True,
            source_url=record.capture.url,
            collection_method=record.capture.collection_method,
            requirements=parse_job_description(
                record.capture.description or record.capture.visible_text
            ).required_skills,
            job_text=record.capture.description or record.capture.visible_text,
            resume_text=self._load_context().resume_text,
            source_capture_id=record.id,
            trace={
                "provider_requested": str(summary.get("provider", "local")),
                "provider_used": str(summary.get("provider", "local")),
                "fallback_used": bool(summary.get("fallback_used", False)),
            },
        )
        self.capture_store.save(
            record.model_copy(update={"status": "tracked", "tracker_id": tracked.id})
        )
        return CompanionResponse(
            message="Vaga enviada ao tracker.",
            capture_id=record.id,
            match_score=analysis.match_score,
            ats_score=analysis.ats_score,
            recommendation=analysis.recommendation,
            provider=str(summary.get("provider", "local")),
            tracker_id=tracked.id,
            snapshot_id=record.snapshot_id,
        )

    def import_applications(self, payload: ApplicationBatchPayload) -> CompanionResponse:
        """Import jobs already applied to from a manually opened tracker page."""
        tracker_ids: list[str] = []
        known_ids = {record.id for record in self.tracker.list_analyses()}
        new_count = 0
        for capture in payload.applications:
            clean = sanitize_capture(capture)
            response = self.capture_job(clean)
            parsed = parse_job_description(clean.description or clean.visible_text)
            saved = self.tracker.add_existing_application(
                job_title=clean.job_title or clean.page_title,
                company=clean.company,
                source_url=clean.url,
                notes="Importada de uma lista de candidaturas pela extensão assistiva.",
                collection_method="browser_assisted_capture",
                requirements=parsed.required_skills,
                modality="" if parsed.modality == "unknown" else parsed.modality,
                seniority=parsed.seniority,
            )
            tracker_ids.append(saved.id)
            if saved.id not in known_ids:
                known_ids.add(saved.id)
                new_count += 1
            record = self.capture_store.get(response.capture_id)
            if record is not None:
                self.capture_store.save(
                    record.model_copy(update={"status": "tracked", "tracker_id": saved.id})
                )
        return CompanionResponse(
            message=(
                f"{len(tracker_ids)} candidaturas processadas: {new_count} novas e "
                f"{len(tracker_ids) - new_count} já existentes."
            ),
            tracker_id=tracker_ids[-1],
        )

    def analyze_project_capture(
        self, payload: ProjectAnalysisPayload, *, save_to_memory: bool = True
    ) -> ProjectCompanionResponse:
        """Analyze and optionally persist a public GitHub/project/portfolio capture."""
        report = self._analyze_project_or_repository(payload)
        extension_report = payload.analysis_result.get("extension_ai_report")
        if isinstance(extension_report, dict):
            report = _merge_extension_ai_report(report, extension_report)
        elif payload.analysis_result.get("use_ai") is True:
            report = enhance_project_report(payload, report)
        self.project_store.save(ProjectAnalysisRecord(payload=payload, report=report))
        if save_to_memory:
            self.memory.remember_project_analysis(report)
        return ProjectCompanionResponse(
            message="Projeto analisado e salvo no SotuHire.",
            report=report,
            saved_to_memory=save_to_memory,
        )

    def _analyze_project_or_repository(
        self,
        payload: ProjectAnalysisPayload,
    ) -> ProjectAnalysisReport:
        """Use GitHub Analyzer 2 when requested, preserving the legacy fallback."""
        use_github_api = payload.analysis_result.get("use_github_api") is True
        if payload.page_type == "github_repo" and use_github_api:
            try:
                github_report = analyze_github_repository(
                    payload.url or f"https://github.com/{payload.owner}/{payload.repo}",
                    fallback_payload=payload,
                )
                return project_report_from_github_analysis(github_report, payload)
            except GitHubAnalyzerError:
                pass
        return analyze_project(payload.model_copy(update={"provider_used": "local"}))

    def _resolve_record(self, request: CaptureActionRequest) -> CompanionCaptureRecord:
        if request.capture is not None:
            response = self.capture_job(request.capture)
            record = self.capture_store.get(response.capture_id)
        else:
            record = self.capture_store.get(request.capture_id)
        if record is None:
            raise KeyError("Captura não encontrada.")
        return record

    def _load_context(self) -> CompanionAnalysisContext:
        if not self.context_path.exists():
            return CompanionAnalysisContext()
        try:
            return CompanionAnalysisContext.model_validate_json(
                self.context_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return CompanionAnalysisContext()


class LocalCompanionApp:
    """Minimal request router shared by HTTP and unit tests."""

    def __init__(
        self, service: LocalCompanionService | None = None, *, token: str | None = None
    ) -> None:
        self.service = service or LocalCompanionService()
        self.token = configured_token() if token is None else token

    def handle(
        self,
        method: str,
        path: str,
        *,
        body: bytes = b"",
        client_host: str = "127.0.0.1",
        token: str = "",
    ) -> tuple[int, dict[str, object]]:
        if not is_local_client(client_host):
            return 403, {"ok": False, "message": "A Local API aceita somente localhost."}
        if not token_is_valid(token, self.token):
            return 401, {"ok": False, "message": "Token local inválido."}
        try:
            if method == "GET" and path == "/health":
                return 200, self.service.health().model_dump(mode="json")
            if method == "GET" and path in {"/capture/status", "/capture/context-summary"}:
                return 200, self.service.context_summary().model_dump(mode="json")
            payload = json.loads(body.decode("utf-8") or "{}")
            if method == "POST" and path == "/handshake":
                response = self.service.handshake(CompanionHandshakeRequest.model_validate(payload))
            elif method == "POST" and path == "/capture/job":
                response = self.service.capture_job(BrowserCapturePayload.model_validate(payload))
            elif method == "POST" and path == "/capture/public-exam":
                response = self.service.capture_public_exam(
                    BrowserCapturePayload.model_validate(payload)
                )
            elif method == "POST" and path == "/capture/analyze":
                response = self.service.analyze_capture(
                    CaptureActionRequest.model_validate(payload)
                )
            elif method == "POST" and path == "/capture/tracker":
                response = self.service.track_capture(CaptureActionRequest.model_validate(payload))
            elif method == "POST" and path == "/capture/applications":
                response = self.service.import_applications(
                    ApplicationBatchPayload.model_validate(payload)
                )
            elif method == "POST" and path in {
                "/capture/github-profile",
                "/capture/github-repo",
                "/capture/portfolio",
                "/capture/project",
                "/capture/repo-analysis",
                "/capture/commit-analysis",
            }:
                response = self.service.analyze_project_capture(
                    ProjectAnalysisPayload.model_validate(payload)
                )
            else:
                return 404, {"ok": False, "message": "Endpoint não encontrado."}
            return 200, response.model_dump(mode="json")
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            return 422, {"ok": False, "message": str(exc)}
        except KeyError as exc:
            return 404, {"ok": False, "message": str(exc)}


def _merge_extension_ai_report(
    local: ProjectAnalysisReport,
    external: dict[str, object],
) -> ProjectAnalysisReport:
    """Keep deterministic scores while consuming reviewed qualitative extension output."""
    provider = str(external.get("provider_used", "")).strip().lower()
    if provider not in {"gemini", "openai", "local-browser", "local"}:
        provider = "local"

    def strings(key: str) -> list[str]:
        value = external.get(key, [])
        if not isinstance(value, list):
            return []
        return [
            sanitize_text(item, limit=2_000)
            for item in value[:20]
            if isinstance(item, str) and item.strip()
        ]

    updates: dict[str, object] = {"provider_used": provider}
    summary = external.get("summary")
    if isinstance(summary, str) and summary.strip():
        updates["summary"] = sanitize_text(summary, limit=5_000)
    for key in (
        "strengths",
        "weaknesses",
        "priority_recommendations",
        "resume_highlights",
    ):
        values = strings(key)
        if values:
            updates[key] = values
    stack = strings("stack")
    if stack:
        updates["stack"] = list(dict.fromkeys([*local.stack, *stack]))[:30]
    return local.model_copy(update=updates)


def _summary_int(summary: dict[str, object], key: str) -> int:
    value = summary.get(key, 0)
    return value if isinstance(value, int) else 0
