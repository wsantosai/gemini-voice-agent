import asyncio
import json
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

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "loan_reminder.md"

# --- Mock data ---

MOCK_CUSTOMERS = {
    "CC-1234567": {
        "customer_id": "CC-1234567",
        "name": "Carlos Andrés Mejía",
        "loan_id": "LOAN-88421",
        "product": "Crédito de libre inversión",
        "total_amount": 15_000_000,
        "monthly_payment": 650_000,
        "pending_amount": 650_000,
        "due_date": "2026-03-15",
        "days_overdue": 15,
        "payments_made": 8,
        "total_payments": 24,
        "interest_rate": "1.2% MV",
        "late_fee": 45_000,
    }
}

MOCK_PAYMENT_OPTIONS = {
    "LOAN-88421": [
        {"method": "PSE", "description": "Transferencia bancaria por PSE, se refleja en 24 horas"},
        {"method": "Corresponsal bancario", "description": "Pago en Efecty, Baloto o puntos Bancolombia, se refleja en 48 horas"},
        {"method": "Débito automático", "description": "Se programa desde la app, se descuenta el día que usted elija"},
        {"method": "Oficina", "description": "En cualquier sucursal con su número de cédula"},
    ]
}


def handle_tool_call(name: str, args: dict) -> dict:
    """Route mock tool calls and return fake data."""
    if name == "get_loan_details":
        customer_id = args.get("customer_id", "CC-1234567")
        data = MOCK_CUSTOMERS.get(customer_id)
        if data:
            return {"status": "found", "data": data}
        return {"status": "not_found", "message": "Cliente no encontrado"}

    if name == "get_payment_options":
        loan_id = args.get("loan_id", "LOAN-88421")
        options = MOCK_PAYMENT_OPTIONS.get(loan_id, [])
        return {"status": "ok", "options": options}

    if name == "register_payment_promise":
        return {
            "status": "registered",
            "confirmation_code": "PROM-2026-0330-001",
            "message": f"Promesa de pago registrada: ${args.get('amount', 0):,} para el {args.get('date', 'N/A')}",
        }

    return {"status": "error", "message": f"Unknown tool: {name}"}


def load_system_prompt() -> str:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def build_tools() -> list[types.Tool]:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="get_loan_details",
                    description="Retrieve loan and payment details for a customer by their ID number (cédula)",
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer ID (cédula), e.g. CC-1234567",
                            }
                        },
                        "required": ["customer_id"],
                    },
                ),
                types.FunctionDeclaration(
                    name="get_payment_options",
                    description="Get available payment methods for a given loan",
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "loan_id": {
                                "type": "string",
                                "description": "The loan identifier, e.g. LOAN-88421",
                            }
                        },
                        "required": ["loan_id"],
                    },
                ),
                types.FunctionDeclaration(
                    name="register_payment_promise",
                    description="Register the customer's commitment to pay by a specific date and amount",
                    parameters_json_schema={
                        "type": "object",
                        "properties": {
                            "loan_id": {
                                "type": "string",
                                "description": "The loan identifier",
                            },
                            "date": {
                                "type": "string",
                                "description": "Promised payment date in YYYY-MM-DD format",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Amount the customer promises to pay in COP",
                            },
                        },
                        "required": ["loan_id", "date", "amount"],
                    },
                ),
            ]
        )
    ]


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
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
            ),
        ),
        input_audio_transcription={},
        output_audio_transcription={},
        tools=build_tools(),
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
        print("Connected. Agent will start speaking...\n")

        # Agent speaks first — simulate outbound call
        await session.send_realtime_input(
            text=(
                "You are calling customer Carlos Andrés Mejía (CC-1234567). "
                "Start the call now: greet him, introduce yourself as Carolina "
                "from the financial institution, confirm his identity, and then "
                "use get_loan_details to look up his account. Be warm and professional."
            )
        )

        async def send_audio():
            while True:
                chunk = await asyncio.to_thread(mic.read, CHUNK, False)
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                )

        async def receive_audio():
            while True:
                async for response in session.receive():
                    # Handle tool calls
                    if response.tool_call:
                        function_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"  [tool] {fc.name}({json.dumps(fc.args, ensure_ascii=False)})")
                            result = handle_tool_call(fc.name, fc.args)
                            print(f"  [tool] -> {json.dumps(result, ensure_ascii=False)}")
                            function_responses.append(
                                types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response=result,
                                )
                            )
                        await session.send_tool_response(
                            function_responses=function_responses
                        )
                        continue

                    # Handle audio and transcripts
                    content = response.server_content
                    if content:
                        if content.input_transcription:
                            print(f"  Customer: {content.input_transcription.text}")
                        if content.output_transcription:
                            print(f"  Carolina: {content.output_transcription.text}")
                        if content.model_turn:
                            for part in content.model_turn.parts:
                                if part.inline_data:
                                    speaker.write(part.inline_data.data)
                        if content.interrupted:
                            pass

        await asyncio.gather(send_audio(), receive_audio())


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nCall ended.")


if __name__ == "__main__":
    main()
