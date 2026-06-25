"""Summarizer agent powered by Anthropic Claude."""

from __future__ import annotations

import json
import os
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv


class Summarizer:
    """Creates a structured meeting summary from a transcript."""

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def run(self, transcript: str) -> dict[str, Any]:
        prompt = f"""
You are a meeting summarization agent.

Return JSON only. Do not include markdown, explanations, or code fences.

Schema:
{{
  "meeting_title": "string",
  "attendees_mentioned": ["string"],
  "key_decisions_made": ["string"],
  "topics_discussed": ["string"],
  "follow_up_meetings": [
    {{
      "title": "string",
      "date": "ISO-8601 datetime or null",
      "description": "string"
    }}
  ]
}}

If no follow-up meetings are mentioned, use an empty list.
If a date is ambiguous or missing, use null.

Transcript:
{transcript}
""".strip()

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_json(self._text_from_response(response))

    def _text_from_response(self, response: Any) -> str:
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()

    def _parse_json(self, text: str) -> dict[str, Any]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Summarizer returned invalid JSON: {text}") from exc

        required = {
            "meeting_title",
            "attendees_mentioned",
            "key_decisions_made",
            "topics_discussed",
            "follow_up_meetings",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"Summarizer JSON missing keys: {', '.join(missing)}")
        return data

