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

# Set your API key
export GOOGLE_API_KEY="your-key-here"
```

## Usage

```bash
uv run python -m src.agent
```

Speak into your microphone. The agent responds through your speakers. Transcripts print to the terminal. Press `Ctrl+C` to quit.

## System Prompt

Edit `prompts/system_prompt.md` to customize the agent's behavior. The file is loaded at startup — no code changes needed.

## Project Structure

```
gemini-voice-agent/
├── pyproject.toml          # project config & dependencies
├── prompts/
│   └── system_prompt.md    # agent personality & rules
├── docs/
│   └── gemini-live-api.md  # API research & reference
└── src/
    └── agent.py            # voice agent script
```

## Docs

See `docs/gemini-live-api.md` for Gemini Live API research notes, competitor comparison, configuration options, and reference links.
