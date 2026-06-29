"""Local notification endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.routes.responses import ok
from apps.api.schemas.common import ApiEnvelope
from apps.api.schemas.notifications import (
    NotificationBulkResponse,
    NotificationPatchRequest,
    NotificationResponse,
    NotificationsResponse,
)
from apps.api.services.notifications import (
    notification_patch,
    notifications_delete_read,
    notifications_list,
    notifications_mark_all_read,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=ApiEnvelope[NotificationsResponse])
def list_notifications(unread_only: bool = False) -> ApiEnvelope[NotificationsResponse]:
    """List local in-app notifications."""
    return ok(notifications_list(unread_only=unread_only))


@router.patch("/{notification_id}", response_model=ApiEnvelope[NotificationResponse])
def patch_notification(
    notification_id: str,
    payload: NotificationPatchRequest,
) -> ApiEnvelope[NotificationResponse]:
    """Mark a notification as read or dismissed."""
    return ok(notification_patch(notification_id, payload), request_id=payload.request_id)


@router.post("/mark-all-read", response_model=ApiEnvelope[NotificationBulkResponse])
def mark_all_read() -> ApiEnvelope[NotificationBulkResponse]:
    """Mark all notifications as read."""
    return ok(notifications_mark_all_read())


@router.delete("/read", response_model=ApiEnvelope[NotificationBulkResponse])
def delete_read() -> ApiEnvelope[NotificationBulkResponse]:
    """Delete read notifications."""
    return ok(notifications_delete_read())
