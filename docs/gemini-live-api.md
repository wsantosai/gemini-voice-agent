# Gemini Live API — Research Notes

## Overview

The Gemini Live API enables low-latency, real-time voice interactions using a native audio-to-audio model. Unlike traditional STT -> LLM -> TTS pipelines, Gemini processes and generates audio in a single model pass over a persistent WebSocket connection.

## Model

| Model | ID | Notes |
|---|---|---|
| Gemini 3.1 Flash Live | `gemini-3.1-flash-live-preview` | Recommended. Optimized for real-time dialogue, acoustic nuance, numeric precision |

## Audio Format

| Direction | Format | Sample Rate | Encoding |
|---|---|---|---|
| Input (mic) | Raw PCM | 16kHz | 16-bit little-endian mono |
| Output (speaker) | Raw PCM | 24kHz | 16-bit little-endian mono |

MIME type for input: `audio/pcm;rate=16000`

## Key Configuration Options

### LiveConnectConfig

```python
from google.genai import types

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction="Your system prompt here",
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
    thinking_config=types.ThinkingConfig(thinking_level="low"),
    input_audio_transcription={},
    output_audio_transcription={},
)
```

### Available Voices

Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus

### VAD (Voice Activity Detection)

Automatic by default. Configurable:

```python
"realtime_input_config": {
    "automatic_activity_detection": {
        "disabled": False,
        "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
        "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
        "prefix_padding_ms": 20,
        "silence_duration_ms": 100,
    }
}
```

### Transcription

Enable input/output transcripts as a side channel:

```python
config = {
    "response_modalities": ["AUDIO"],
    "input_audio_transcription": {},
    "output_audio_transcription": {},
}
```

### Interruptions (Barge-in)

The model supports barge-in natively. When the user starts speaking while the model is responding, the model stops. Handle via:

```python
async for response in session.receive():
    if response.server_content and response.server_content.interrupted is True:
        # Stop audio playback
        pass
```

## Competitor Comparison

| | Gemini Live | OpenAI Realtime | ElevenLabs Agents | Inworld |
|---|---|---|---|---|
| Architecture | Native audio-to-audio | Native audio-to-audio | Pipeline (STT->LLM->TTS) | Native audio-to-audio |
| Latency (e2e) | 320-800ms | ~500-1000ms | ~600-1000ms+ | Similar to Gemini |
| Multilingual | 70 languages | Good | Good | Less tested |
| Spanish (LATAM) | Very good | Good | Good | Less tested |
| Function calling | Yes | Yes (strong) | Yes | Yes |
| Model flexibility | Yes | Locked to GPT-4o | Choose your LLM | Yes |
| Voice quality | Good | Good | Best in class | Good |
| Pricing | Low | High | Medium | Medium |

### ElevenLabs Pipeline Breakdown

ElevenLabs does NOT use native audio-to-audio. Their pipeline:

```
Audio -> STT (Scribe, ~200-300ms)
      -> LLM (your choice, ~300-600ms)
      -> TTS (Flash v2.5, ~75ms)
      = Total: ~600-1000ms+
```

The 75ms figure often cited is TTS-only, not end-to-end.

### Half-Cascade Architecture

For maximum voice quality with low latency, combine:
- **Gemini Live** for audio understanding (native, fast)
- **ElevenLabs TTS** for audio output (best voice quality)

This requires LiveKit or a similar WebRTC framework to orchestrate.

## API Reference Links

- [Gemini Live API Overview](https://ai.google.dev/gemini-api/docs/live-api)
- [Live API Capabilities Guide](https://ai.google.dev/gemini-api/docs/live-guide)
- [Get Started with GenAI SDK](https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk)
- [python-genai SDK (PyPI)](https://pypi.org/project/google-genai/)
- [python-genai source (GitHub)](https://github.com/googleapis/python-genai)
- [Gemini Live API Examples (GitHub)](https://github.com/google-gemini/gemini-live-api-examples)
- [Gemini 3.1 Flash Live Model Card](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-live-preview)
