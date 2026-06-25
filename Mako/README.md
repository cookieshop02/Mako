# Mako

A sequential multi-agent meeting-to-action pipeline in Python:

1. Transcribe audio locally with OpenAI Whisper.
2. Summarize the transcript with Claude.
3. Extract structured action items with Claude.
4. Dispatch follow-up Google Calendar events and a Gmail report.
5. Save a local `meeting_report.md` even if Google API calls fail.

## Project Structure

```text
Mako/
|-- main.py
|-- agents/
|   |-- transcriber.py
|   |-- summarizer.py
|   |-- action_extractor.py
|   `-- dispatcher.py
|-- tools/
|   |-- whisper_tool.py
|   |-- calendar_tool.py
|   `-- gmail_tool.py
|-- orchestrator.py
|-- requirements.txt
`-- README.md
```

## Setup

```bash
cd Mako
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set:

```text
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Whisper runs locally and requires `ffmpeg` to be available on your system path.

## Google OAuth Setup

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable these APIs:
   - Google Calendar API
   - Gmail API
4. Configure the OAuth consent screen.
5. Create OAuth client credentials:
   - Application type: Desktop app
6. Download the client secret file and save it as `credentials.json` in the `Mako` directory.

The app requests only these scopes:

```text
https://www.googleapis.com/auth/calendar.events
https://www.googleapis.com/auth/gmail.send
```

On first run, a browser OAuth flow opens and writes `token.json`. Keep `credentials.json`, `token.json`, and `.env` private.

## Usage

Run from audio:

```bash
python main.py --audio meeting.mp3 --email you@example.com
```

Run from an existing transcript and skip transcription:

```bash
python main.py --transcript transcript.txt --email you@example.com
```

Optional flags:

```bash
python main.py --audio meeting.m4a --email you@example.com --output reports/meeting_report.md --whisper-model small
```

Supported audio formats are `.mp3`, `.wav`, and `.m4a`.

## Sample Output

Console:

```text
[1/4] Transcribing or loading transcript...
[2/4] Summarizing meeting with Claude...
[3/4] Extracting action items with Claude...
[4/4] Dispatching calendar and email actions...
  - Calendar created: Product Review Follow-up
  - Email sent: you@example.com
Done. Saved report to meeting_report.md
```

`meeting_report.md`:

```markdown
# Product Planning Sync

## Summary

{
  "meeting_title": "Product Planning Sync",
  "attendees_mentioned": ["Priya", "Alex"],
  "key_decisions_made": ["Ship the onboarding flow first."],
  "topics_discussed": ["Launch timeline", "Beta feedback"],
  "follow_up_meetings": [
    {
      "title": "Product Review Follow-up",
      "date": "2026-07-02T15:00:00",
      "description": "Review onboarding metrics and remaining launch blockers."
    }
  ]
}

## Action Items

| Task | Assigned Person | Due Date | Priority |
| --- | --- | --- | --- |
| Draft beta launch checklist | Priya | 2026-06-28 | High |
```

## Notes

- The pipeline is intentionally sequential: Transcribe -> Summarize -> Extract Actions -> Dispatch.
- Summarizer and Action Extractor ask Claude for JSON only and parse responses with `json.loads()`.
- Calendar and Gmail failures are logged but do not prevent the local report from being saved.
- If your OAuth scopes change after `token.json` is created, delete `token.json` and run the app again.
