import asyncio
import os
from pathlib import Path

import pyaudio
from dotenv import load_dotenv

load_dotenv()
from google import genai
from google.genai import types

INPUT_RATE = 16000
OUTPUT_RATE = 24000
CHUNK = 1024
MODEL = "gemini-3.1-flash-live-preview"

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "system_prompt.md"


def load_system_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    # Strip the markdown title (first H1 line) — send only the body
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


async def run():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: set GOOGLE_API_KEY environment variable")
        print("  Get one at https://aistudio.google.com/apikey")
        return

    client = genai.Client(api_key=api_key)
    system_prompt = load_system_prompt()

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=system_prompt,
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
            ),
            language_code="es-US",
        ),
        input_audio_transcription={},
        output_audio_transcription={},
    )

    audio = pyaudio.PyAudio()

    mic = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=INPUT_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    speaker = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=OUTPUT_RATE,
        output=True,
    )

    print(f"Connecting to {MODEL}...")

    async with client.aio.live.connect(model=MODEL, config=config) as session:
        print("Connected. Speak now (Ctrl+C to quit).\n")

        async def send_audio():
            while True:
                chunk = await asyncio.to_thread(mic.read, CHUNK, False)
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                )

        async def receive_audio():
            while True:
                async for response in session.receive():
                    content = response.server_content
                    if content:
                        if content.input_transcription:
                            print(f"  You: {content.input_transcription.text}")
                        if content.output_transcription:
                            print(f"  Agent: {content.output_transcription.text}")
                        if content.model_turn:
                            for part in content.model_turn.parts:
                                if part.inline_data:
                                    speaker.write(part.inline_data.data)
                        if content.interrupted:
                            pass  # barge-in: model stops, playback clears naturally

        await asyncio.gather(send_audio(), receive_audio())


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nSession ended.")


if __name__ == "__main__":
    main()
