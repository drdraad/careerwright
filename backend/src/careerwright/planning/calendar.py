"""Portable calendar dates from one saved plan; no external calendar is changed."""

import uuid
from datetime import UTC, timedelta

from careerwright.planning.plan_records import PlanSnapshot, review_event


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _fold(line: str) -> list[str]:
    """RFC 5545's 75-octet content lines, including UTF-8 and continuation spaces."""
    parts: list[str] = []
    current = ""
    for char in line:
        limit = 75 if not parts else 74
        if len((current + char).encode("utf-8")) > limit:
            parts.append(current)
            current = char
        else:
            current += char
    parts.append(current)
    return [parts[0], *(" " + part for part in parts[1:])]


def calendar_text(plan: PlanSnapshot) -> str:
    """Actual dates are all-day events with exclusive ends; model months create none."""
    synthetic = plan.route.basis.synthetic or plan.route.label.synthetic
    revised_at = (
        max(plan.selected_at, plan.progress.activity[-1].recorded_at)
        if plan.progress.activity
        else plan.selected_at
    )
    stamp = revised_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Careerwright//Plan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-TIMEZONE:Europe/London",
    ]
    review = review_event(plan.progress)
    for event in [*plan.events, *([review] if review else [])]:
        if event.kind != "review" and event.variant_id in plan.progress.completed_steps:
            continue
        uid = uuid.uuid5(plan.plan_id, event.key)
        if event.kind == "review":
            summary = "Review this plan"
            description = "A planning review date you recorded; no external calendar has changed."
        else:
            kind = event.kind.replace("_", " ")
            label = "Proposed, conditional" if event.conditional else "Proposed"
            summary = _escape(f"{label}: {event.title} — {kind}")
            description = _escape(
                "A proposed plan date. Confirm the conditions before acting."
                if event.conditional
                else "A proposed plan date; no booking or application has been made."
            )
        if synthetic:
            summary = f"Synthetic demo: {summary}"
            description = f"Synthetic demo data. {description}"
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}@careerwright.local",
                f"SEQUENCE:{plan.version - 1}",
                f"DTSTAMP:{stamp}",
                f"LAST-MODIFIED:{stamp}",
                f"DTSTART;VALUE=DATE:{event.on:%Y%m%d}",
                f"DTEND;VALUE=DATE:{event.on + timedelta(days=1):%Y%m%d}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(part for line in lines for part in _fold(line)) + "\r\n"
