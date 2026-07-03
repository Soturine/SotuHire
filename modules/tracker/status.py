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


class PublicOpportunityStatus(StrEnum):
    """Prepared statuses for public exams without changing the private-job Kanban."""

    NOTICED = "noticed"
    REVIEWING_NOTICE = "reviewing_notice"
    REQUIREMENTS_REVIEW = "requirements_review"
    REGISTERED_MANUALLY = "registered_manually"
    STUDYING = "studying"
    EXAM_SCHEDULED = "exam_scheduled"
    DOCUMENT_PENDING = "document_pending"
    RESULT_WAITING = "result_waiting"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
