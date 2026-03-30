# gemini-voice-agent

Real-time voice agent using the Gemini Live API. Captures microphone input, streams it to Gemini, and plays back audio responses through your speakers.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- PortAudio (for PyAudio):
  ```bash
  brew install portaudio   # macOS
  ```
- A Google AI API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Setup

```bash
cd gemini-voice-agent

# Create venv and install deps
uv sync

# Configure your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## Usage

### Generic voice agent

```bash
uv run python -m src.agent
```

Speak into your microphone. The agent responds through your speakers. Transcripts print to the terminal. Press `Ctrl+C` to quit.

### Loan payment reminder (POC)

```bash
uv run python -m src.loan_reminder
```

Simulates an outbound collections call. The agent (Carolina) initiates the conversation, looks up the customer's loan via mock tool calls, and guides them toward a payment commitment. Tool calls and transcripts print to the terminal.

Mock tools:
- `get_loan_details` — retrieves customer loan info
- `get_payment_options` — lists available payment methods
- `register_payment_promise` — logs the customer's payment commitment

## System Prompts

Edit the markdown files in `prompts/` to customize agent behavior — loaded at startup, no code changes needed.

- `prompts/system_prompt.md` — generic voice assistant (Colombian Spanish)
- `prompts/loan_reminder.md` — loan payment reminder agent

## Project Structure

```
gemini-voice-agent/
├── .env.example                # API key template
├── pyproject.toml              # uv project config & dependencies
├── prompts/
│   ├── system_prompt.md        # generic agent personality & rules
│   └── loan_reminder.md        # loan reminder call flow & tone
├── docs/
│   └── gemini-live-api.md      # API research & reference
└── src/
    ├── agent.py                # generic voice agent
    └── loan_reminder.py        # loan reminder POC with mock tools
```

## Docs

See `docs/gemini-live-api.md` for Gemini Live API research notes, competitor comparison, configuration options, and reference links.
