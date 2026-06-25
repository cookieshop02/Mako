"""Dispatcher agent for calendar and email side effects."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

try:
    from ..tools.calendar_tool import create_calendar_event
    from ..tools.gmail_tool import send_gmail
except ImportError:
    from tools.calendar_tool import create_calendar_event
    from tools.gmail_tool import send_gmail


class Dispatcher:
    """Creates follow-up calendar events and sends a Gmail report."""

    def __init__(self, *, credentials_path: Path, token_path: Path) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path

    async def run(
        self,
        *,
        action_items: list[dict[str, Any]],
        summary: dict[str, Any],
        transcript: str,
        recipient_email: str,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {"calendar_events": [], "email": None}

        for follow_up in summary.get("follow_up_meetings", []):
            title = follow_up.get("title")
            date = follow_up.get("date")
            description = follow_up.get("description") or ""
            if not title or not date:
                results["calendar_events"].append(
                    {
                        "title": title,
                        "date": date,
                        "success": False,
                        "error": "Missing title or date; skipped calendar event.",
                    }
                )
                print(f"  - Calendar skipped: {title or 'Untitled follow-up'}")
                continue

            try:
                event = await asyncio.to_thread(
                    create_calendar_event,
                    title,
                    date,
                    description,
                    str(self.credentials_path),
                    str(self.token_path),
                )
                results["calendar_events"].append(
                    {"title": title, "date": date, "success": True, "event": event}
                )
                print(f"  - Calendar created: {title}")
            except Exception as exc:  # Keep report generation resilient.
                results["calendar_events"].append(
                    {
                        "title": title,
                        "date": date,
                        "success": False,
                        "error": str(exc),
                    }
                )
                print(f"  - Calendar failed: {title} ({exc})")

        subject = f"Meeting Report: {summary.get('meeting_title') or 'Untitled Meeting'}"
        body = self._build_email_body(
            summary=summary,
            action_items=action_items,
            transcript=transcript,
        )
        try:
            message = await asyncio.to_thread(
                send_gmail,
                recipient_email,
                subject,
                body,
                str(self.credentials_path),
                str(self.token_path),
            )
            results["email"] = {
                "to": recipient_email,
                "success": True,
                "message": message,
            }
            print(f"  - Email sent: {recipient_email}")
        except Exception as exc:  # Keep report generation resilient.
            results["email"] = {
                "to": recipient_email,
                "success": False,
                "error": str(exc),
            }
            print(f"  - Email failed: {recipient_email} ({exc})")

        return results

    def _build_email_body(
        self,
        *,
        summary: dict[str, Any],
        action_items: list[dict[str, Any]],
        transcript: str,
    ) -> str:
        return "\n".join(
            [
                f"Meeting: {summary.get('meeting_title') or 'Untitled Meeting'}",
                "",
                "Summary JSON:",
                json.dumps(summary, indent=2, ensure_ascii=False),
                "",
                "Action Items JSON:",
                json.dumps(action_items, indent=2, ensure_ascii=False),
                "",
                "Transcript:",
                transcript,
            ]
        )

