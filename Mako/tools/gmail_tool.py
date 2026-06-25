"""Gmail sending tool."""

from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import Any

from googleapiclient.discovery import build

try:
    from .google_auth import REQUIRED_GOOGLE_SCOPES, get_credentials
except ImportError:
    from google_auth import REQUIRED_GOOGLE_SCOPES, get_credentials


def send_gmail(
    to: str,
    subject: str,
    body: str,
    credentials_path: str = "credentials.json",
    token_path: str = "token.json",
) -> dict[str, Any]:
    """Send a plain-text Gmail message and return the API response."""
    creds = get_credentials(
        credentials_path=credentials_path,
        token_path=token_path,
        scopes=REQUIRED_GOOGLE_SCOPES,
    )
    service = build("gmail", "v1", credentials=creds)

    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded})
        .execute()
    )
