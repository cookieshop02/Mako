"""Sequential orchestration for the meeting-to-action pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .agents.action_extractor import ActionExtractor
    from .agents.dispatcher import Dispatcher
    from .agents.summarizer import Summarizer
    from .agents.transcriber import Transcriber
except ImportError:  # Allows `python main.py` from inside meeting_agent/.
    from agents.action_extractor import ActionExtractor
    from agents.dispatcher import Dispatcher
    from agents.summarizer import Summarizer
    from agents.transcriber import Transcriber


class MeetingOrchestrator:
    """Runs Transcribe -> Summarize -> Extract Actions -> Dispatch."""

    def __init__(
        self,
        *,
        output_path: Path,
        recipient_email: str,
        google_credentials_path: Path,
        google_token_path: Path,
        whisper_model: str = "base",
    ) -> None:
        self.output_path = output_path
        self.recipient_email = recipient_email
        self.transcriber = Transcriber(model_name=whisper_model)
        self.summarizer = Summarizer()
        self.action_extractor = ActionExtractor()
        self.dispatcher = Dispatcher(
            credentials_path=google_credentials_path,
            token_path=google_token_path,
        )

    async def run(
        self,
        *,
        audio_path: Path | None = None,
        transcript_path: Path | None = None,
    ) -> dict[str, Any]:
        print("[1/4] Transcribing or loading transcript...")
        transcript = await self._get_transcript(audio_path, transcript_path)

        print("[2/4] Summarizing meeting with Claude...")
        summary = await self.summarizer.run(transcript)

        print("[3/4] Extracting action items with Claude...")
        action_items = await self.action_extractor.run(transcript)

        print("[4/4] Dispatching calendar and email actions...")
        dispatch_results = await self.dispatcher.run(
            action_items=action_items,
            summary=summary,
            transcript=transcript,
            recipient_email=self.recipient_email,
        )

        report = self._render_report(
            transcript=transcript,
            summary=summary,
            action_items=action_items,
            dispatch_results=dispatch_results,
        )
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(report, encoding="utf-8")
        print(f"Done. Saved report to {self.output_path}")

        return {
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "dispatch_results": dispatch_results,
            "report_path": str(self.output_path),
        }

    async def _get_transcript(
        self,
        audio_path: Path | None,
        transcript_path: Path | None,
    ) -> str:
        if transcript_path:
            if transcript_path.suffix.lower() != ".txt":
                raise ValueError("--transcript must point to a .txt file.")
            if not transcript_path.exists():
                raise FileNotFoundError(f"Transcript not found: {transcript_path}")
            transcript = transcript_path.read_text(encoding="utf-8").strip()
            if not transcript:
                raise ValueError(f"Transcript file is empty: {transcript_path}")
            return transcript

        if audio_path is None:
            raise ValueError("Provide either --audio or --transcript.")
        return await self.transcriber.run(audio_path)

    def _render_report(
        self,
        *,
        transcript: str,
        summary: dict[str, Any],
        action_items: list[dict[str, Any]],
        dispatch_results: dict[str, Any],
    ) -> str:
        return "\n".join(
            [
                f"# {summary.get('meeting_title') or 'Meeting Report'}",
                "",
                "## Summary",
                "",
                "```json",
                json.dumps(summary, indent=2, ensure_ascii=False),
                "```",
                "",
                "## Action Items",
                "",
                self._render_action_items(action_items),
                "",
                "## Dispatch Results",
                "",
                "```json",
                json.dumps(dispatch_results, indent=2, ensure_ascii=False),
                "```",
                "",
                "## Transcript",
                "",
                transcript,
                "",
            ]
        )

    def _render_action_items(self, action_items: list[dict[str, Any]]) -> str:
        if not action_items:
            return "No action items found."

        rows = [
            "| Task | Assigned Person | Due Date | Priority |",
            "| --- | --- | --- | --- |",
        ]
        for item in action_items:
            rows.append(
                "| {task} | {person} | {due} | {priority} |".format(
                    task=self._md_cell(item.get("task_description")),
                    person=self._md_cell(item.get("assigned_person")),
                    due=self._md_cell(item.get("due_date")),
                    priority=self._md_cell(item.get("priority")),
                )
            )
        return "\n".join(rows)

    def _md_cell(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).replace("|", "\\|").replace("\n", " ")

