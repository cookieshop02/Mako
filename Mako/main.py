"""CLI entry point for the meeting-to-action pipeline."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

try:
    from .orchestrator import MeetingOrchestrator
except ImportError:  # Allows `python main.py` from inside meeting_agent/.
    from orchestrator import MeetingOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a meeting-to-action pipeline from audio or a transcript."
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--audio",
        type=Path,
        help="Path to an audio file (.mp3, .wav, .m4a) to transcribe locally.",
    )
    source_group.add_argument(
        "--transcript",
        type=Path,
        help="Path to a .txt transcript file. Skips transcription.",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Recipient email address for the Gmail summary report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("meeting_report.md"),
        help="Path for the generated Markdown report.",
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=Path("credentials.json"),
        help="Path to Google OAuth credentials JSON.",
    )
    parser.add_argument(
        "--token",
        type=Path,
        default=Path("token.json"),
        help="Path where Google OAuth token JSON is stored.",
    )
    parser.add_argument(
        "--whisper-model",
        default="base",
        help="Local Whisper model name to use when --audio is provided.",
    )
    parser.add_argument(
        "--provider",
        choices=("anthropic", "groq", "local"),
        default="anthropic",
        help="LLM provider for summary/action extraction.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Shortcut for --provider local.",
    )
    parser.add_argument(
        "--no-dispatch",
        action="store_true",
        help="Skip Google Calendar and Gmail calls. Useful for local testing.",
    )
    return parser


async def async_main() -> None:
    args = build_parser().parse_args()
    provider = "local" if args.offline else args.provider
    orchestrator = MeetingOrchestrator(
        output_path=args.output,
        recipient_email=args.email,
        google_credentials_path=args.credentials,
        google_token_path=args.token,
        whisper_model=args.whisper_model,
        provider=provider,
        no_dispatch=args.no_dispatch,
    )
    await orchestrator.run(audio_path=args.audio, transcript_path=args.transcript)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(async_main())
