"""SQLite outcome events and deterministic exploratory aggregates."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from modules.storage.ai_runs import sanitize_error_message
from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database

from .models import OutcomeEvent, OutcomeGroup, OutcomeRate, OutcomeSummary, ScoreOutcomeSignal

SampleConfidence = Literal["insufficient", "indicative", "comparable"]


def sample_confidence(sample_size: int) -> SampleConfidence:
    if sample_size < 5:
        return "insufficient"
    if sample_size < 20:
        return "indicative"
    return "comparable"


class OutcomeStore:
    """Persist explicit events and calculate non-causal, sample-labelled signals."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )

    def save(self, event: OutcomeEvent) -> OutcomeEvent:
        ensure_database(self.database_path)
        safe = event.model_copy(
            update={
                "source": sanitize_error_message(event.source),
                "resume_variant_id": sanitize_error_message(event.resume_variant_id),
                "metadata": _safe_metadata(event.metadata),
            }
        )
        with connect_database(self.database_path) as connection:
            application = connection.execute(
                "SELECT 1 FROM applications WHERE id = ?", (safe.application_id,)
            ).fetchone()
            if application is None:
                raise LookupError("Application not found")
            connection.execute(
                """INSERT INTO outcome_events
                (event_id, application_id, event_type, occurred_at, source, resume_variant_id,
                 match_score, ats_score, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    safe.event_id,
                    safe.application_id,
                    safe.event_type,
                    safe.occurred_at.isoformat(),
                    safe.source,
                    safe.resume_variant_id,
                    safe.match_score,
                    safe.ats_score,
                    json.dumps(safe.metadata, ensure_ascii=False, sort_keys=True),
                    safe.created_at.isoformat(),
                ),
            )
        return safe

    def for_application(self, application_id: str) -> list[OutcomeEvent]:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """SELECT * FROM outcome_events WHERE application_id = ?
                ORDER BY occurred_at, created_at""",
                (application_id,),
            ).fetchall()
        return [_from_row(row) for row in rows]

    def list(self) -> list[OutcomeEvent]:
        ensure_database(self.database_path)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM outcome_events ORDER BY occurred_at, created_at"
            ).fetchall()
        return [_from_row(row) for row in rows]

    def summary(self) -> OutcomeSummary:
        events = self.list()
        by_application: dict[str, list[OutcomeEvent]] = defaultdict(list)
        for event in events:
            by_application[event.application_id].append(event)
        sample_size = len(by_application)
        responses = _applications_with(by_application, {"response_received"})
        interviews = _applications_with(
            by_application, {"interview_scheduled", "interview_completed"}
        )
        offers = _applications_with(by_application, {"offer_received"})
        summary = OutcomeSummary(
            sample_size=sample_size,
            confidence=sample_confidence(sample_size),
            response_rate=_rate(len(responses), sample_size, "resposta"),
            interview_rate=_rate(len(interviews), sample_size, "entrevista"),
            offer_rate=_rate(len(offers), sample_size, "oferta"),
            average_time_to_response_hours=_average_time_to_response(by_application),
            average_time_in_stage_hours=_average_stage_time(by_application),
            source_effectiveness=_groups(by_application, "source"),
            resume_variant_effectiveness=_groups(by_application, "resume_variant_id"),
            match_score_vs_outcome=_score_signal(
                events, "match_score", responses | interviews | offers
            ),
            ats_score_vs_outcome=_score_signal(
                events, "ats_score", responses | interviews | offers
            ),
        )
        self._cache_summary(summary)
        return summary

    def _cache_summary(self, summary: OutcomeSummary) -> None:
        calculated_at = datetime.now().astimezone().isoformat()
        metrics = {
            "response_rate": summary.response_rate.value,
            "interview_rate": summary.interview_rate.value,
            "offer_rate": summary.offer_rate.value,
        }
        with connect_database(self.database_path) as connection:
            for name, value in metrics.items():
                connection.execute(
                    """INSERT INTO outcome_metrics
                    (metric_id, scope_type, scope_id, metric_name, value, sample_size,
                     confidence, calculated_at)
                    VALUES (?, 'global', '', ?, ?, ?, ?, ?)
                    ON CONFLICT(scope_type, scope_id, metric_name) DO UPDATE SET
                        value=excluded.value, sample_size=excluded.sample_size,
                        confidence=excluded.confidence, calculated_at=excluded.calculated_at""",
                    (
                        f"global:{name}",
                        name,
                        value,
                        summary.sample_size,
                        summary.confidence,
                        calculated_at,
                    ),
                )


def _rate(numerator: int, denominator: int, label: str) -> OutcomeRate:
    confidence = sample_confidence(denominator)
    value = numerator / denominator if denominator else 0.0
    note = f"{numerator} de {denominator} candidaturas tiveram {label}. " + (
        "Amostra pequena; use como sinal exploratório."
        if denominator < 5
        else "Não demonstra causalidade."
    )
    return OutcomeRate(
        value=value,
        numerator=numerator,
        denominator=denominator,
        sample_size=denominator,
        confidence=confidence,
        note=note,
    )


def _applications_with(events: dict[str, list[OutcomeEvent]], event_types: set[str]) -> set[str]:
    return {
        application_id
        for application_id, items in events.items()
        if any(item.event_type in event_types for item in items)
    }


def _groups(events: dict[str, list[OutcomeEvent]], field: str) -> list[OutcomeGroup]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for application_id, items in events.items():
        key = next((str(getattr(item, field)) for item in items if getattr(item, field)), "")
        if key:
            grouped[key].add(application_id)
    result: list[OutcomeGroup] = []
    for key, applications in sorted(grouped.items()):
        selected = {application_id: events[application_id] for application_id in applications}
        responses = len(_applications_with(selected, {"response_received"}))
        interviews = len(
            _applications_with(selected, {"interview_scheduled", "interview_completed"})
        )
        offers = len(_applications_with(selected, {"offer_received"}))
        result.append(
            OutcomeGroup(
                key=key,
                applications=len(applications),
                responses=responses,
                interviews=interviews,
                offers=offers,
                response_rate=responses / len(applications),
                confidence=sample_confidence(len(applications)),
            )
        )
    return result


def _score_signal(
    events: list[OutcomeEvent], field: str, successful_applications: set[str]
) -> ScoreOutcomeSignal:
    scores: dict[str, float] = {}
    for event in events:
        value = getattr(event, field)
        if value is not None and event.application_id not in scores:
            scores[event.application_id] = float(value)
    successful = [value for key, value in scores.items() if key in successful_applications]
    other = [value for key, value in scores.items() if key not in successful_applications]
    return ScoreOutcomeSignal(
        sample_size=len(scores),
        successful_average=mean(successful) if successful else None,
        other_average=mean(other) if other else None,
        confidence=sample_confidence(len(scores)),
    )


def _average_time_to_response(events: dict[str, list[OutcomeEvent]]) -> float | None:
    durations: list[float] = []
    for items in events.values():
        submitted = next(
            (
                item.occurred_at
                for item in items
                if item.event_type == "application_submitted_manually"
            ),
            None,
        )
        response = next(
            (item.occurred_at for item in items if item.event_type == "response_received"), None
        )
        if submitted and response and response >= submitted:
            durations.append((response - submitted).total_seconds() / 3600)
    return mean(durations) if durations else None


def _average_stage_time(events: dict[str, list[OutcomeEvent]]) -> float | None:
    durations: list[float] = []
    for items in events.values():
        for left, right in zip(items, items[1:], strict=False):
            if right.occurred_at >= left.occurred_at:
                durations.append((right.occurred_at - left.occurred_at).total_seconds() / 3600)
    return mean(durations) if durations else None


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    allowed = {"channel", "reason_category", "manual_note_present"}
    return {
        key: value
        for key, value in metadata.items()
        if key in allowed and isinstance(value, (str, bool, int, float, type(None)))
    }


def _from_row(row: Any) -> OutcomeEvent:
    return OutcomeEvent(
        event_id=row["event_id"],
        application_id=row["application_id"],
        event_type=row["event_type"],
        occurred_at=row["occurred_at"],
        source=row["source"],
        resume_variant_id=row["resume_variant_id"],
        match_score=row["match_score"],
        ats_score=row["ats_score"],
        metadata=json.loads(row["metadata"]),
        created_at=row["created_at"],
    )


__all__ = ["OutcomeStore", "SampleConfidence", "sample_confidence"]
