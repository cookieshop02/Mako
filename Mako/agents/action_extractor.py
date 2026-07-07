"""Action extractor agent powered by Anthropic Claude."""

from __future__ import annotations

import json
import os
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv


class ActionExtractor:
    """Extracts action items from a meeting transcript."""

    VALID_PRIORITIES = {"High", "Medium", "Low"}

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def run(self, transcript: str) -> list[dict[str, Any]]:
        prompt = f"""
        You are an action item extraction agent.
        
        Return JSON only. Do not include markdown, explanations, or code fences.
        
        Return an array. Each item must match this schema:
        {{
          "task_description": "string",
          "assigned_person": "string or null",
          "due_date": "ISO-8601 date/datetime string or null",
          "priority": "High | Medium | Low"
        }}
        
        Infer due dates and priority only when reasonable from the transcript.
        Use null for missing assigned people or due dates.
        If no action items are present, return [].
        
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

    def _parse_json(self, text: str) -> list[dict[str, Any]]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Action extractor returned invalid JSON: {text}") from exc

        if not isinstance(data, list):
            raise ValueError("Action extractor JSON must be an array.")

        for index, item in enumerate(data):
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
        return data

