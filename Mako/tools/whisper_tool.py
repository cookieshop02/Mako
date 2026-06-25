"""Local OpenAI Whisper transcription helper."""

from __future__ import annotations


def transcribe_audio(file_path: str, model_name: str = "base") -> str:
    """Run local Whisper transcription and return plain text."""
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(file_path)
    return str(result.get("text", "")).strip()

