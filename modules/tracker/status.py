"""Typed statuses for the local application tracker."""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    """Supported user-controlled tracker states."""

    FOUND = "found"
    ANALYZED = "analyzed"
    GOOD_FIT = "good_fit"
    APPLIED = "applied"
    MESSAGE_SENT = "message_sent"
    FOLLOW_UP = "follow_up"
    INTERVIEW = "interview"
    TECHNICAL_TEST = "technical_test"
    REJECTED = "rejected"
    OFFER = "offer"
    ARCHIVED = "archived"
