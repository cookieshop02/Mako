"""Transcriber agent."""

from __future__ import annotations

import asyncio
from pathlib import Path

try:
    from ..tools.whisper_tool import transcribe_audio
except ImportError:
    from tools.whisper_tool import transcribe_audio


class Transcriber:
    """Transcribes local audio using OpenAI Whisper."""

    SUPPORTED_SUFFIXES = {".mp3", ".wav", ".m4a"}

    def __init__(self, model_name: str = "base") -> None:
        self.model_name = model_name

    async def run(self, file_path: Path) -> str:
        if file_path.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            allowed = ", ".join(sorted(self.SUPPORTED_SUFFIXES))
            raise ValueError(f"Unsupported audio file type. Use one of: {allowed}")
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        transcript = await asyncio.to_thread(
            transcribe_audio,
            str(file_path),
            self.model_name,
        )
        if not transcript.strip():
            raise ValueError("Whisper returned an empty transcript.")
        return transcript.strip()

