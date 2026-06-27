"""Free local action extractor used when Anthropic credits are unavailable."""

from __future__ import annotations

import re
from typing import Any


class LocalActionExtractor:
    """Extracts obvious action items without external API calls."""

    async def run(self, transcript: str) -> list[dict[str, Any]]:
        action_items = []
        for sentence in _sentences(transcript):
            item = self._item_from_sentence(sentence)
            if item:
                action_items.append(item)
        return action_items

    def _item_from_sentence(self, sentence: str) -> dict[str, Any] | None:
        patterns = [
            r"(?P<person>[A-Z][a-z]+)\s+will\s+(?P<task>.+)",
            r"(?P<person>[A-Z][a-z]+)\s+needs to\s+(?P<task>.+)",
            r"(?P<person>[A-Z][a-z]+)\s+should\s+(?P<task>.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, sentence)
            if not match:
                continue
            task = match.group("task").strip(" .")
            return {
                "task_description": task,
                "assigned_person": match.group("person"),
                "due_date": _due_date(sentence),
                "priority": _priority(sentence),
            }
        return None


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _due_date(text: str) -> str | None:
    iso_match = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    if iso_match:
        return iso_match.group(0)

    lowered = text.lower()
    for phrase in (
        "today",
        "tomorrow",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "next week",
    ):
        if phrase in lowered:
            return phrase
    return None


def _priority(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("urgent", "critical", "blocker", "asap")):
        return "High"
    if any(word in lowered for word in ("nice to have", "later", "low priority")):
        return "Low"
    return "Medium"

