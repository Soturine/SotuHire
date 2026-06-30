"""Local scheduler for safe recurring Radar runs."""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from time import monotonic

from modules.context import (
    CareerContextEngine,
    CareerContextPurpose,
    context_brief,
    format_context_for_prompt,
)
from modules.radar.models import JobWishlist, RadarResult, RadarSource, utc_now
from modules.radar.notifications import LocalNotificationService
from modules.radar.schedule_models import (
    LocalNotification,
    RadarSchedule,
    RadarScheduledRun,
    RadarSchedulerStatus,
)
from modules.radar.schedule_store import RadarScheduleStore
from modules.radar.service import JobRadarService

SchedulerAiEnricher = Callable[[RadarResult, JobWishlist], dict[str, object]]


class ScheduledRadarService:
    """Manage schedules and execute bounded Radar runs."""

    def __init__(
        self,
        *,
        store: RadarScheduleStore | None = None,
        radar_service: JobRadarService | None = None,
        notifications: LocalNotificationService | None = None,
    ) -> None:
        self.store = store or RadarScheduleStore()
        self.radar_service = radar_service or JobRadarService()
        self.notifications = notifications or LocalNotificationService(self.store)
        self._running_schedule_ids: set[str] = set()
        self._lock = threading.Lock()

    def list_schedules(self) -> list[RadarSchedule]:
        """List schedules newest first."""
        return sorted(self.store.load().schedules, key=lambda item: item.updated_at, reverse=True)

    def get_schedule(self, schedule_id: str) -> RadarSchedule:
        """Return one schedule."""
        for schedule in self.store.load().schedules:
            if schedule.schedule_id == schedule_id:
                return schedule
        raise KeyError("Agendamento nao encontrado.")

    def create_schedule(self, schedule: RadarSchedule) -> RadarSchedule:
        """Create a schedule and compute next run."""
        state = self.store.load()
        now = utc_now()
        created = schedule.model_copy(
            update={
                "created_at": now,
                "updated_at": now,
                "next_run_at": schedule.next_run_at or _next_run_at(schedule, from_time=now),
            }
        )
        state.schedules.append(created)
        self.store.save(state)
        return created

    def update_schedule(self, schedule_id: str, updates: dict[str, object]) -> RadarSchedule:
        """Patch one schedule."""
        state = self.store.load()
        for index, schedule in enumerate(state.schedules):
            if schedule.schedule_id == schedule_id:
                cleaned = {key: value for key, value in updates.items() if value is not None}
                updated = schedule.model_copy(update={**cleaned, "updated_at": utc_now()})
                if "frequency" in cleaned or "interval_minutes" in cleaned or "enabled" in cleaned:
                    updated = updated.model_copy(
                        update={"next_run_at": _next_run_at(updated, from_time=utc_now())}
                    )
                state.schedules[index] = updated
                self.store.save(state)
                return updated
        raise KeyError("Agendamento nao encontrado.")

    def delete_schedule(self, schedule_id: str) -> RadarSchedule:
        """Disable one schedule without deleting run history."""
        return self.update_schedule(schedule_id, {"enabled": False})

    def list_scheduled_runs(self) -> list[RadarScheduledRun]:
        """List scheduled run history."""
        return sorted(
            self.store.load().scheduled_runs, key=lambda item: item.started_at, reverse=True
        )

    def status(self, *, running: bool = False) -> RadarSchedulerStatus:
        """Return scheduler runtime status."""
        state = self.store.load()
        enabled = [item for item in state.schedules if item.enabled]
        now = utc_now()
        next_run = min((item.next_run_at for item in enabled if item.next_run_at), default=None)
        due = sum(1 for item in enabled if item.next_run_at and item.next_run_at <= now)
        return RadarSchedulerStatus(
            running=running,
            enabled_schedules=len(enabled),
            total_schedules=len(state.schedules),
            next_run_at=next_run,
            due_schedules=due,
        )

    def run_due_once(
        self,
        *,
        ai_enricher: SchedulerAiEnricher | None = None,
        now: datetime | None = None,
    ) -> list[RadarScheduledRun]:
        """Execute schedules due at the current time."""
        current = now or utc_now()
        due = [
            schedule
            for schedule in self.store.load().schedules
            if schedule.enabled and schedule.next_run_at and schedule.next_run_at <= current
        ]
        runs: list[RadarScheduledRun] = []
        for schedule in due:
            runs.append(
                self.run_schedule(schedule.schedule_id, manual=False, ai_enricher=ai_enricher)
            )
        return runs

    def run_schedule(
        self,
        schedule_id: str,
        *,
        manual: bool = True,
        ai_enricher: SchedulerAiEnricher | None = None,
    ) -> RadarScheduledRun:
        """Run one schedule. Manual runs are allowed outside quiet hours."""
        schedule = self.get_schedule(schedule_id)
        if not schedule.enabled:
            return self._record_skipped(schedule, "Agendamento pausado.")
        if not manual and _in_quiet_hours(schedule, utc_now()):
            return self._record_skipped(schedule, "Horario silencioso ativo.")
        with self._lock:
            if schedule.schedule_id in self._running_schedule_ids:
                return self._record_skipped(schedule, "Agendamento ja esta em execucao.")
            self._running_schedule_ids.add(schedule.schedule_id)
        started = monotonic()
        scheduled_run = RadarScheduledRun(
            schedule_id=schedule.schedule_id,
            status="running",
            manual=manual,
            metadata={
                "frequency": schedule.frequency,
                "source_ids": schedule.source_ids,
                "wishlist_id": schedule.wishlist_id,
                "auto_apply": False,
                "review_required": True,
            },
        )
        notifications_created: list[LocalNotification] = []
        warnings: list[str] = []
        profile_text = ""
        context_summary = ""
        try:
            if schedule.use_profile_context:
                context = _career_context_for_schedule(schedule)
                profile_text = format_context_for_prompt(context, include_sensitive=False)
                context_summary = context_brief(context)
                if profile_text:
                    warnings.append("Career Context Engine aplicado localmente ao Radar agendado.")
                warnings.extend(context.warnings)
            auth_sources = _authenticated_assisted_sources(
                self.radar_service.list_sources(),
                schedule.source_ids,
            )
            for source in auth_sources:
                notification = self.notifications.create(
                    title="Captura assistida autenticada agendada",
                    message=(
                        f"Abra e revise manualmente a fonte {source.name}. "
                        "O SotuHire nao coleta cookies, tokens, sessao ou headers."
                    ),
                    severity="info",
                    notification_type="assisted_capture_schedule",
                    related_entity_type="radar_source",
                    related_entity_id=source.id,
                    metadata={
                        "schedule_id": schedule.schedule_id,
                        "source_type": source.source_type,
                        "review_required": True,
                    },
                    cooldown_key=f"assisted:{schedule.schedule_id}:{source.id}",
                    cooldown_minutes=schedule.cooldown_minutes,
                )
                if notification:
                    notifications_created.append(notification)
            radar_run, results, alerts, radar_warnings = self.radar_service.run(
                source_ids=schedule.source_ids,
                wishlist_id=schedule.wishlist_id or "",
                resume_text=profile_text,
                keywords=schedule.keywords,
                use_ai=schedule.use_ai,
                ai_enricher=ai_enricher if schedule.use_ai else None,
            )
            warnings.extend(radar_warnings)
            if schedule.notify_on_new_matches and results:
                notification = self.notifications.create(
                    title=f"{len(results)} resultado(s) do Radar agendado",
                    message=_matches_notification_message(schedule.name, context_summary),
                    severity="success" if alerts else "info",
                    related_entity_type="radar_schedule",
                    related_entity_id=schedule.schedule_id,
                    metadata={
                        "schedule_id": schedule.schedule_id,
                        "radar_run_id": radar_run.id,
                        "alerts": len(alerts),
                        "auto_apply": False,
                        "context_summary": context_summary,
                    },
                    cooldown_key=f"matches:{schedule.schedule_id}",
                    cooldown_minutes=schedule.cooldown_minutes,
                )
                if notification:
                    notifications_created.append(notification)
            if radar_run.errors:
                notification = self.notifications.create(
                    title="Radar agendado encontrou erro de fonte",
                    message="Revise as fontes do agendamento antes da proxima execucao.",
                    severity="warning",
                    related_entity_type="radar_schedule",
                    related_entity_id=schedule.schedule_id,
                    metadata={"schedule_id": schedule.schedule_id, "errors": radar_run.errors[:3]},
                    cooldown_key=f"errors:{schedule.schedule_id}",
                    cooldown_minutes=schedule.cooldown_minutes,
                )
                if notification:
                    notifications_created.append(notification)
            scheduled_run = scheduled_run.model_copy(
                update={
                    "finished_at": utc_now(),
                    "status": "warning" if warnings or radar_run.errors else "success",
                    "total_results": len(results),
                    "new_results": sum(1 for item in results if item.radar_status != "duplicate"),
                    "alerts_created": len(notifications_created),
                    "warnings": [*warnings, *radar_run.errors],
                    "radar_run_id": radar_run.id,
                    "profile_context_used": bool(profile_text),
                    "metadata": {
                        **scheduled_run.metadata,
                        "duration_ms": int((monotonic() - started) * 1000),
                        "radar_alerts": len(alerts),
                        "context_summary": context_summary,
                    },
                }
            )
            self._persist_run(schedule, scheduled_run)
            return scheduled_run
        except Exception as exc:
            scheduled_run = scheduled_run.model_copy(
                update={
                    "finished_at": utc_now(),
                    "status": "error",
                    "error": str(exc),
                    "warnings": warnings,
                }
            )
            self.notifications.create(
                title="Radar agendado falhou",
                message=str(exc)[:500],
                severity="error",
                related_entity_type="radar_schedule",
                related_entity_id=schedule.schedule_id,
                metadata={"schedule_id": schedule.schedule_id},
                cooldown_key=f"fatal:{schedule.schedule_id}",
                cooldown_minutes=schedule.cooldown_minutes,
            )
            self._persist_run(schedule, scheduled_run)
            return scheduled_run
        finally:
            with self._lock:
                self._running_schedule_ids.discard(schedule.schedule_id)

    def _record_skipped(self, schedule: RadarSchedule, reason: str) -> RadarScheduledRun:
        skipped = RadarScheduledRun(
            schedule_id=schedule.schedule_id,
            status="skipped",
            finished_at=utc_now(),
            warnings=[reason],
            metadata={"review_required": True},
        )
        self._persist_run(schedule, skipped)
        return skipped

    def _persist_run(self, schedule: RadarSchedule, run: RadarScheduledRun) -> None:
        state = self.store.load()
        state.scheduled_runs.append(run)
        next_run = _next_run_at(schedule, from_time=utc_now())
        for index, current in enumerate(state.schedules):
            if current.schedule_id == schedule.schedule_id:
                state.schedules[index] = current.model_copy(
                    update={
                        "last_run_at": run.started_at,
                        "next_run_at": next_run,
                        "updated_at": utc_now(),
                    }
                )
                break
        self.store.save(state)


class RadarSchedulerRuntime:
    """Tiny in-process loop used while the local API is running."""

    def __init__(self, service: ScheduledRadarService | None = None) -> None:
        self.service = service or ScheduledRadarService()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self, *, ai_enricher: SchedulerAiEnricher | None = None) -> RadarSchedulerStatus:
        """Start background polling if not already running."""
        if self.is_running:
            return self.status()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            kwargs={"ai_enricher": ai_enricher},
            name="sotuhire-radar-scheduler",
            daemon=True,
        )
        self._thread.start()
        return self.status()

    def stop(self) -> RadarSchedulerStatus:
        """Stop background polling."""
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        return self.status()

    @property
    def is_running(self) -> bool:
        """Return whether the scheduler thread is alive."""
        return bool(self._thread and self._thread.is_alive() and not self._stop.is_set())

    def status(self) -> RadarSchedulerStatus:
        """Return current runtime and schedule status."""
        return self.service.status(running=self.is_running)

    def _loop(self, *, ai_enricher: SchedulerAiEnricher | None) -> None:
        while not self._stop.is_set():
            self.service.run_due_once(ai_enricher=ai_enricher)
            self._stop.wait(30)


def _next_run_at(schedule: RadarSchedule, *, from_time: datetime) -> datetime | None:
    if not schedule.enabled:
        return None
    if schedule.frequency == "hourly":
        return from_time + timedelta(hours=1)
    if schedule.frequency == "daily":
        return from_time + timedelta(days=1)
    if schedule.frequency == "weekly":
        return from_time + timedelta(weeks=1)
    return from_time + timedelta(minutes=schedule.interval_minutes or 60)


def _in_quiet_hours(schedule: RadarSchedule, now: datetime) -> bool:
    if not schedule.quiet_hours_start or not schedule.quiet_hours_end:
        return False
    start = _minutes(schedule.quiet_hours_start)
    end = _minutes(schedule.quiet_hours_end)
    current = now.hour * 60 + now.minute
    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


def _minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def _career_context_for_schedule(schedule: RadarSchedule):
    return CareerContextEngine().build(
        CareerContextPurpose.RADAR,
        query=" ".join([schedule.name, *schedule.keywords]),
        max_evidence=10,
    )


def _matches_notification_message(schedule_name: str, context_summary: str) -> str:
    if context_summary:
        return (
            f"{schedule_name} encontrou oportunidades para revisao manual "
            f"alinhadas a {context_summary}."
        )[:1_000]
    return f"{schedule_name} encontrou oportunidades para revisao manual."


def _authenticated_assisted_sources(
    sources: list[RadarSource],
    source_ids: list[str],
) -> list[RadarSource]:
    wanted = set(source_ids)
    return [
        source
        for source in sources
        if source.source_type == "authenticated_assisted_capture"
        and source.is_active
        and (not wanted or source.id in wanted)
    ]
