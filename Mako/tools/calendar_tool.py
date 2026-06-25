"""Google Calendar tool."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

try:
    from .google_auth import REQUIRED_GOOGLE_SCOPES, get_credentials
except ImportError:
    from google_auth import REQUIRED_GOOGLE_SCOPES, get_credentials


def create_calendar_event(
    title: str,
    date: str,
    description: str,
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
) -> dict[str, Any]:
    """Create a one-hour Google Calendar event and return the API response."""
    creds = get_credentials(
        credentials_path=credentials_path,
        token_path=token_path,
        scopes=REQUIRED_GOOGLE_SCOPES,
    )
    service = build("calendar", "v3", credentials=creds)

    start = _parse_datetime(date)
    end = start + timedelta(hours=1)
    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
    }
    return service.events().insert(calendarId="primary", body=event).execute()


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed
    return parsed.astimezone().replace(tzinfo=None)
