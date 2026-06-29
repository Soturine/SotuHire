"""Local in-app notifications for Radar workflows."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from modules.radar.models import utc_now
from modules.radar.schedule_models import LocalNotification, NotificationSeverity
from modules.radar.schedule_store import RadarScheduleStore


class LocalNotificationService:
    """Create and update local notifications without external delivery."""

    def __init__(self, store: RadarScheduleStore | None = None) -> None:
        self.store = store or RadarScheduleStore()

    def list_notifications(
        self,
        *,
        unread_only: bool = False,
        include_dismissed: bool = False,
    ) -> list[LocalNotification]:
        """List notifications newest first."""
        notifications = self.store.load().notifications
        if unread_only:
            notifications = [item for item in notifications if item.read_at is None]
        if not include_dismissed:
            notifications = [item for item in notifications if item.dismissed_at is None]
        return sorted(notifications, key=lambda item: item.created_at, reverse=True)

    def create(
        self,
        *,
        title: str,
        message: str,
        severity: NotificationSeverity = "info",
        notification_type: str = "radar_schedule",
        source: str = "radar",
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        cooldown_key: str | None = None,
        cooldown_minutes: int = 0,
    ) -> LocalNotification | None:
        """Create notification unless cooldown suppresses it."""
        state = self.store.load()
        now = utc_now()
        metadata = dict(metadata or {})
        if cooldown_key:
            threshold = now - timedelta(minutes=cooldown_minutes)
            for item in state.notifications:
                if (
                    item.metadata.get("cooldown_key") == cooldown_key
                    and item.created_at >= threshold
                ):
                    return None
            metadata["cooldown_key"] = cooldown_key
        notification = LocalNotification(
            type=notification_type,
            title=title,
            message=message,
            severity=severity,
            source=source,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            metadata=metadata,
        )
        state.notifications.append(notification)
        self.store.save(state)
        return notification

    def mark_read(self, notification_id: str) -> LocalNotification:
        """Mark one notification as read."""
        state = self.store.load()
        for index, item in enumerate(state.notifications):
            if item.notification_id == notification_id:
                updated = item.model_copy(update={"read_at": item.read_at or utc_now()})
                state.notifications[index] = updated
                self.store.save(state)
                return updated
        raise KeyError("Notificacao nao encontrada.")

    def dismiss(self, notification_id: str) -> LocalNotification:
        """Dismiss one notification without deleting history."""
        state = self.store.load()
        for index, item in enumerate(state.notifications):
            if item.notification_id == notification_id:
                updated = item.model_copy(update={"dismissed_at": item.dismissed_at or utc_now()})
                state.notifications[index] = updated
                self.store.save(state)
                return updated
        raise KeyError("Notificacao nao encontrada.")

    def mark_all_read(self) -> int:
        """Mark all visible notifications as read."""
        state = self.store.load()
        count = 0
        updated_notifications = []
        for item in state.notifications:
            if item.read_at is None and item.dismissed_at is None:
                item = item.model_copy(update={"read_at": utc_now()})
                count += 1
            updated_notifications.append(item)
        state.notifications = updated_notifications
        self.store.save(state)
        return count

    def delete_read(self) -> int:
        """Remove read notifications from local store."""
        state = self.store.load()
        before = len(state.notifications)
        state.notifications = [item for item in state.notifications if item.read_at is None]
        self.store.save(state)
        return before - len(state.notifications)
