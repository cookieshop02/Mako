"""Free local summarizer used when Anthropic credits are unavailable."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class LocalSummarizer:
    """Creates a simple structured summary without external API calls."""

    async def run(self, transcript: str) -> dict[str, Any]:
        sentences = _sentences(transcript)
        return {
            "meeting_title": self._title_from_text(transcript),
            "attendees_mentioned": self._attendees(transcript),
            "key_decisions_made": self._decisions(sentences),
            "topics_discussed": self._topics(sentences),
            "follow_up_meetings": self._follow_ups(sentences),
        }

    def _title_from_text(self, transcript: str) -> str:
        lowered = transcript.lower()
        if "launch" in lowered:
            return "Launch Planning Meeting"
        if "onboarding" in lowered:
            return "Onboarding Review Meeting"
        if "budget" in lowered:
            return "Budget Review Meeting"
        return "Meeting Report"

    def _attendees(self, transcript: str) -> list[str]:
        candidates = re.findall(r"\b[A-Z][a-z]{2,}\b", transcript)
        ignored = {
            "Today",
            "Tomorrow",
            "Friday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Saturday",
            "Sunday",
            "UTC",
        }
        names = []
        for candidate in candidates:
            if candidate not in ignored and candidate not in names:
                names.append(candidate)
        return names[:10]

    def _decisions(self, sentences: list[str]) -> list[str]:
        decision_words = ("decided", "agreed", "approved", "confirmed")
        return [s for s in sentences if any(word in s.lower() for word in decision_words)]

    def _topics(self, sentences: list[str]) -> list[str]:
        topics = []
        keywords = [
            "launch",
            "onboarding",
            "beta",
            "bugs",
            "timeline",
            "budget",
            "follow-up",
            "meeting",
        ]
        lowered = " ".join(sentences).lower()
        for keyword in keywords:
            if keyword in lowered:
                topics.append(keyword.title())
        return topics or ["General discussion"]

    def _follow_ups(self, sentences: list[str]) -> list[dict[str, Any]]:
        follow_ups = []
        for sentence in sentences:
            lowered = sentence.lower()
            if "follow-up" not in lowered and "follow up" not in lowered:
                continue
            date = _find_iso_datetime(sentence)
            follow_ups.append(
                {
                    "title": "Follow-up Meeting",
                    "date": date,
                    "description": sentence,
                }
            )
        return follow_ups


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _find_iso_datetime(text: str) -> str | None:
    date_match = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    if not date_match:
        return None

    time_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if not time_match:
        return date_match.group(0)

    value = f"{date_match.group(0)}T{time_match.group(0)}:00"
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return date_match.group(0)
    return value

