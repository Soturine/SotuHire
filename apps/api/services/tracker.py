"""Tracker service used by API routes."""

from __future__ import annotations

from fastapi import HTTPException
from modules.context import CareerContext, CareerContextEngine, CareerContextPurpose, context_brief
from modules.core.text_utils import normalize_text
from modules.schemas.job_analysis import JobAnalysisSchema
from modules.storage.models import StoredAnalysis, utc_now
from modules.tracker.dashboard import (
    calculate_application_funnel,
    calculate_dashboard_metrics,
    calculate_source_metrics,
    rank_critical_gaps,
    rank_missing_requirements,
    rank_requirements_by_source,
    rank_requirements_by_status,
)
from modules.tracker.job_tracker import JobTracker
from modules.tracker.status import JobStatus

from apps.api.schemas.analysis import (
    CriticalGapItem,
    FunnelConversion,
    FunnelStage,
    RequirementBySourceItem,
    RequirementRankItem,
    SourceMetricsItem,
    TrackerFunnelResponse,
    TrackerJobContext,
    TrackerJobCreateRequest,
    TrackerJobResponse,
    TrackerJobsResponse,
    TrackerMetricsResponse,
    TrackerRequirementsResponse,
    TrackerSourcesResponse,
)


class TrackerService:
    """Small adapter over JobTracker for frontend API contracts."""

    def __init__(self, tracker: JobTracker | None = None) -> None:
        self.tracker = tracker or JobTracker()

    def list_jobs(self) -> TrackerJobsResponse:
        """Return local tracker cards."""
        records = self.tracker.list_analyses()
        context = _tracker_context(records)
        return TrackerJobsResponse(
            jobs=records,
            context_summary=context_brief(context),
            job_contexts={record.id: _job_context(record, context) for record in records},
        )

    def create_job(self, request: TrackerJobCreateRequest) -> TrackerJobResponse:
        """Create or update a tracker card."""
        analysis = JobAnalysisSchema(
            match_score=request.match_score,
            ats_score=request.ats_score,
            opportunity_fit_score=request.opportunity_fit_score,
            risk_score=request.risk_score,
            recommendation=request.recommendation,
            missing_keywords=request.requirements,
        )
        try:
            saved = self.tracker.add_analysis(
                analysis=analysis,
                job_title=request.title,
                company=request.company,
                modality=request.modality,
                seniority=request.seniority,
                notes=request.notes,
                privacy_acknowledged=request.privacy_acknowledged,
                source_url=request.source_url,
                collection_method=request.collection_method,
                requirements=request.requirements,
            )
            if saved.status != request.status:
                saved = self.tracker.change_status(saved.id, request.status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        context = _tracker_context([saved])
        return TrackerJobResponse(job=saved, **_job_context(saved, context).model_dump())

    def update_job(
        self,
        record_id: str,
        *,
        status: JobStatus | None = None,
        notes: str | None = None,
    ) -> TrackerJobResponse:
        """Update status and notes for a tracker card."""
        try:
            record = (
                self.tracker.change_status(record_id, status) if status else self._get(record_id)
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if notes is not None and notes != record.notes:
            record.notes = notes
            record.updated_at = utc_now()
            record = self.tracker.store.save(record)
        context = _tracker_context([record])
        return TrackerJobResponse(job=record, **_job_context(record, context).model_dump())

    def metrics(self) -> TrackerMetricsResponse:
        """Return dashboard and frontend KPI aggregates."""
        records = self.tracker.list_analyses()
        metrics = calculate_dashboard_metrics(records)
        by_status = _status_counts(records)
        average_by_status = _average_match_by_status(records)
        funnel = calculate_application_funnel(records)
        stages = {stage.status: stage.count for stage in funnel.stages}
        return TrackerMetricsResponse(
            metrics=metrics,
            total_saved=len(records),
            total_applied=stages.get("applied", 0),
            by_status=by_status,
            average_match_by_status=average_by_status,
            response_rate=_rate(stages.get("response", 0), stages.get("applied", 0)),
            interview_rate=_rate(stages.get("interview", 0), stages.get("applied", 0)),
            offer_rate=_rate(stages.get("offer", 0), stages.get("saved", 0)),
        )

    def requirements(self) -> TrackerRequirementsResponse:
        """Return Application Intelligence requirement aggregates."""
        records = self.tracker.list_analyses()
        return TrackerRequirementsResponse(
            top_requirements=[
                RequirementRankItem(
                    name=name,
                    count=count,
                    status_scope="all",
                    sources=_sources_for_requirement(records, name),
                    candidate_has_evidence=_has_candidate_evidence(records, name),
                )
                for name, count in rank_requirements_by_status(records)
            ],
            missing_requirements=[
                _gap_item(name, count, safe_action="Tratar como gap real ate existir evidencia.")
                for name, count in rank_missing_requirements(records)
            ],
            critical_gaps=[
                _gap_item(
                    name, count, safe_action="Priorizar plano de estudo ou projeto com evidencia."
                )
                for name, count in rank_critical_gaps(records)
            ],
            requirements_by_source=[
                RequirementBySourceItem(source=source, requirement=requirement, count=count)
                for source, requirement, count in rank_requirements_by_source(records)
            ],
        )

    def funnel(self) -> TrackerFunnelResponse:
        """Return application funnel aggregates."""
        funnel = calculate_application_funnel(self.tracker.list_analyses())
        return TrackerFunnelResponse(
            stages=[
                FunnelStage(status=stage.status, label=stage.label, count=stage.count)
                for stage in funnel.stages
            ],
            conversion_rates=[
                FunnelConversion(
                    from_status=item.from_status,
                    to_status=item.to_status,
                    rate=item.rate,
                )
                for item in funnel.conversion_rates
            ],
        )

    def sources(self) -> TrackerSourcesResponse:
        """Return source performance aggregates."""
        return TrackerSourcesResponse(
            sources=[
                SourceMetricsItem(
                    name=item.name,
                    saved=item.saved,
                    applied=item.applied,
                    interviews=item.interviews,
                    average_match=item.average_match,
                    top_requirements=item.top_requirements,
                )
                for item in calculate_source_metrics(self.tracker.list_analyses())
            ]
        )

    def _get(self, record_id: str) -> StoredAnalysis:
        record = self.tracker.store.get(record_id)
        if record is None:
            raise KeyError(f"Analise nao encontrada: {record_id}")
        return record


def get_tracker_service() -> TrackerService:
    """FastAPI dependency factory."""
    return TrackerService()


def _status_counts(records: list[StoredAnalysis]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.status.value] = counts.get(record.status.value, 0) + 1
    return counts


def _average_match_by_status(records: list[StoredAnalysis]) -> dict[str, float]:
    grouped: dict[str, list[int]] = {}
    for record in records:
        grouped.setdefault(record.status.value, []).append(record.analysis.match_score)
    return {
        status: round(sum(scores) / len(scores), 1)
        for status, scores in sorted(grouped.items())
        if scores
    }


def _sources_for_requirement(records: list[StoredAnalysis], requirement: str) -> list[str]:
    requirement_key = requirement.casefold()
    sources: list[str] = []
    for source, source_requirement, _ in rank_requirements_by_source(records, limit=500):
        if source_requirement.casefold() == requirement_key:
            sources.append(source)
    return list(dict.fromkeys(sources))


def _has_candidate_evidence(records: list[StoredAnalysis], requirement: str) -> bool:
    key = requirement.casefold()
    for record in records:
        evidence = [
            *record.analysis.matched_requirements,
            *record.analysis.ats_present_keywords,
            *record.analysis.evidence_used,
        ]
        if any(key in item.casefold() or item.casefold() in key for item in evidence):
            return True
    return False


def _gap_item(name: str, count: int, *, safe_action: str) -> CriticalGapItem:
    severity = "high" if count >= 5 else "medium" if count >= 2 else "low"
    return CriticalGapItem(
        name=name,
        count=count,
        severity=severity,
        safe_action=safe_action,
    )


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 2) if denominator else 0


def _tracker_context(records: list[StoredAnalysis]) -> CareerContext:
    query = " ".join(
        [
            *[record.job_title for record in records],
            *[record.company for record in records],
            *[requirement for record in records for requirement in record.requirements],
        ]
    )
    return CareerContextEngine().build(CareerContextPurpose.TRACKER, query=query, max_evidence=10)


def _job_context(record: StoredAnalysis, context: CareerContext) -> TrackerJobContext:
    corpus = normalize_text(
        " ".join(
            [
                record.job_title,
                record.company,
                record.modality,
                record.seniority,
                " ".join(record.requirements),
                " ".join(record.analysis.missing_keywords),
            ]
        )
    )
    matched = [
        item.title
        for item in context.evidence
        if not item.sensitive and normalize_text(item.title) in corpus
    ][:5]
    gaps = _merge_unique(
        [
            *record.analysis.critical_gaps,
            *record.analysis.missing_requirements,
            *record.analysis.missing_keywords,
        ],
        context.constraints,
    )[:8]
    aligned = bool(matched) or any(
        normalize_text(goal) in corpus for goal in [*context.goals, *context.domains]
    )
    fit_reason = (
        "Alinhada com evidencias locais: " + ", ".join(matched)
        if matched
        else "Sem evidencia local forte; revisar Match antes de aplicar."
    )
    return TrackerJobContext(
        context_summary=context_brief(context),
        fit_reason=fit_reason,
        next_action_hint=_next_action_hint(record, aligned, gaps),
        aligned_with_profile=aligned
        if context.evidence or context.goals or context.domains
        else None,
        recurring_gaps=gaps,
    )


def _next_action_hint(record: StoredAnalysis, aligned: bool, gaps: list[str]) -> str:
    if record.status.value in {"applied", "interview", "offer"}:
        return "Registrar feedback e proximo follow-up."
    if gaps:
        return "Validar gaps antes de ajustar curriculo ou aplicar."
    if aligned and record.analysis.should_apply():
        return "Revisar a vaga original e preparar candidatura manual."
    return "Rodar Match/Tailor com evidencias atualizadas antes da proxima acao."


def _merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*primary, *secondary]:
        cleaned = str(item).strip()
        key = normalize_text(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            merged.append(cleaned)
    return merged
