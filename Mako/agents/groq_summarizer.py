"""Summarizer agent powered by Groq."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from groq import AsyncGroq


class GroqSummarizer:
    """Creates a structured meeting summary from a transcript using Groq."""

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = AsyncGroq(api_key=api_key)

    async def run(self, transcript: str) -> dict[str, Any]:
        prompt = f"""
You are a meeting summarization agent.

Return valid JSON only. Do not include markdown, explanations, or code fences.

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

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured meeting summaries as JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return self._parse_json(response.choices[0].message.content or "")

    def _parse_json(self, text: str) -> dict[str, Any]:
        try:
            data = json.loads(_clean_json_text(text))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Groq summarizer returned invalid JSON: {text}") from exc

        required = {
            "meeting_title",
            "attendees_mentioned",
            "key_decisions_made",
            "topics_discussed",
            "follow_up_meetings",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"Groq summarizer JSON missing keys: {', '.join(missing)}")
        return data


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    return fenced.group(1).strip() if fenced else cleaned

