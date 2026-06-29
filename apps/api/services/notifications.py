"""API service for local in-app notifications."""

from __future__ import annotations

from fastapi import HTTPException
from modules.radar import LocalNotificationService

from apps.api.schemas.notifications import (
    NotificationBulkResponse,
    NotificationPatchRequest,
    NotificationResponse,
    NotificationsResponse,
)


def notifications_list(unread_only: bool = False) -> NotificationsResponse:
    """List local notifications."""
    service = LocalNotificationService()
    notifications = service.list_notifications(unread_only=unread_only)
    unread_count = len(service.list_notifications(unread_only=True))
    return NotificationsResponse(notifications=notifications, unread_count=unread_count)


def notification_patch(
    notification_id: str,
    request: NotificationPatchRequest,
) -> NotificationResponse:
    """Patch one notification."""
    service = LocalNotificationService()
    try:
        if request.dismissed:
            notification = service.dismiss(notification_id)
            return NotificationResponse(
                notification=notification, message="Notificacao dispensada."
            )
        if request.read:
            notification = service.mark_read(notification_id)
            return NotificationResponse(
                notification=notification, message="Notificacao marcada como lida."
            )
        notification = next(
            item
            for item in service.list_notifications(include_dismissed=True)
            if item.notification_id == notification_id
        )
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=404, detail="Notificacao nao encontrada.") from exc
    return NotificationResponse(notification=notification, message="Nenhuma alteracao aplicada.")


def notifications_mark_all_read() -> NotificationBulkResponse:
    """Mark every visible notification as read."""
    count = LocalNotificationService().mark_all_read()
    return NotificationBulkResponse(count=count, message=f"{count} notificacao(oes) lida(s).")


def notifications_delete_read() -> NotificationBulkResponse:
    """Delete read notifications."""
    count = LocalNotificationService().delete_read()
    return NotificationBulkResponse(count=count, message=f"{count} notificacao(oes) removida(s).")
