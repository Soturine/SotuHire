"""DTOs for local in-app notifications."""

from __future__ import annotations

from modules.radar.schedule_models import LocalNotification
from pydantic import BaseModel, ConfigDict, Field


class NotificationPatchRequest(BaseModel):
    """Patch one local notification."""

    model_config = ConfigDict(extra="forbid")

    read: bool | None = None
    dismissed: bool | None = None
    request_id: str = Field(default="", max_length=120)


class NotificationsResponse(BaseModel):
    """Local notifications list."""

    model_config = ConfigDict(extra="forbid")

    notifications: list[LocalNotification] = Field(default_factory=list)
    unread_count: int = 0


class NotificationResponse(BaseModel):
    """One local notification response."""

    model_config = ConfigDict(extra="forbid")

    notification: LocalNotification
    message: str = ""


class NotificationBulkResponse(BaseModel):
    """Bulk notification mutation response."""

    model_config = ConfigDict(extra="forbid")

    count: int
    message: str = ""
