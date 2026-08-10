"""RFC 5545-compatible explicit calendar export for local career events."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta


def export_ics_event(
    *,
    entity_type: str,
    entity_id: str,
    title: str,
    starts_at: datetime,
    ends_at: datetime | None = None,
    description: str = "",
    location: str = "",
    generated_at: datetime | None = None,
) -> str:
    """Return a calendar file; callers decide whether and where to import it."""
    if not starts_at.tzinfo or starts_at.utcoffset() is None:
        raise ValueError("A exportacao ICS exige timezone explicito.")
    resolved_end = ends_at or (starts_at + timedelta(hours=1))
    if not resolved_end.tzinfo or resolved_end.utcoffset() is None:
        raise ValueError("O termino do evento ICS exige timezone explicito.")
    stamp = (generated_at or datetime.now(UTC)).astimezone(UTC)
    uid_hash = hashlib.sha256(f"{entity_type}:{entity_id}".encode()).hexdigest()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SotuHire//Career Actions//EN",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{uid_hash}@sotuhire.local",
        f"DTSTAMP:{_utc(stamp)}",
        f"DTSTART:{_utc(starts_at)}",
        f"DTEND:{_utc(resolved_end)}",
        f"SUMMARY:{_escape(title)}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")
    if location:
        lines.append(f"LOCATION:{_escape(location)}")
    lines.extend(["END:VEVENT", "END:VCALENDAR", ""])
    return "\r\n".join(_fold(line) for line in lines)


def _utc(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _fold(line: str) -> str:
    """Fold content lines at 75 UTF-8 octets without splitting a code point."""
    if len(line.encode("utf-8")) <= 75:
        return line
    chunks: list[str] = []
    current = ""
    limit = 75
    for character in line:
        if len((current + character).encode("utf-8")) > limit:
            chunks.append(current)
            current = character
            limit = 74
        else:
            current += character
    chunks.append(current)
    return "\r\n ".join(chunks)


__all__ = ["export_ics_event"]
