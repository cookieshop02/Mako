"""Action extractor agent powered by Groq."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from groq import AsyncGroq


class GroqActionExtractor:
    """Extracts action items from a meeting transcript using Groq."""

    VALID_PRIORITIES = {"High", "Medium", "Low"}

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = AsyncGroq(api_key=api_key)

    async def run(self, transcript: str) -> list[dict[str, Any]]:
        prompt = f"""
You are an action item extraction agent.

Return valid JSON only. Do not include markdown, explanations, or code fences.

Return this object:
{{
  "action_items": [
    {{
      "task_description": "string",
      "assigned_person": "string or null",
      "due_date": "ISO-8601 date/datetime string or null",
      "priority": "High | Medium | Low"
    }}
  ]
}}

Infer due dates and priority only when reasonable from the transcript.
Use null for missing assigned people or due dates.
If no action items are present, return {{"action_items": []}}.

Transcript:
{transcript}
""".strip()

        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You extract meeting action items as JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return self._parse_json(response.choices[0].message.content or "")

    def _parse_json(self, text: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(_clean_json_text(text))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Groq action extractor returned invalid JSON: {text}") from exc

        if not isinstance(data, dict) or "action_items" not in data:
            raise ValueError("Groq action extractor JSON must include action_items.")

        action_items = data["action_items"]
        if not isinstance(action_items, list):
            raise ValueError("action_items must be an array.")

        for index, item in enumerate(action_items):
            if not isinstance(item, dict):
                raise ValueError(f"Action item {index} is not an object.")
            required = {"task_description", "assigned_person", "due_date", "priority"}
            missing = sorted(required - set(item))
            if missing:
                raise ValueError(
                    f"Action item {index} missing keys: {', '.join(missing)}"
                )
            if item["priority"] not in self.VALID_PRIORITIES:
                raise ValueError(
                    f"Action item {index} has invalid priority: {item['priority']}"
                )
        return action_items


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    return fenced.group(1).strip() if fenced else cleaned

