"""Shared Google OAuth helper for Calendar and Gmail tools."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


REQUIRED_GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_credentials(
    *,
    credentials_path: str,
    token_path: str,
    scopes: Sequence[str],
) -> Credentials:
    """Load, refresh, or create OAuth credentials for the requested scopes."""
    credentials_file = Path(credentials_path)
    token_file = Path(token_path)

    if not credentials_file.exists():
        raise FileNotFoundError(
            f"Google OAuth credentials file not found: {credentials_file}"
        )

    creds: Credentials | None = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
        token_scopes = set(creds.scopes or [])
        if token_scopes and not set(scopes).issubset(token_scopes):
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes)
        creds = flow.run_local_server(port=0)

    token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds
