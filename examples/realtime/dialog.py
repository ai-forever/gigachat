"""Run an endless text dialogue over protobuf WebSocket realtime."""

import asyncio
import os
from typing import Any, List
from uuid import uuid4

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models.realtime import OutputAdditionalDataEvent, OutputTranscriptionEvent, RealtimeErrorEvent
from gigachat.types.realtime import RealtimeContextMessageParam, RealtimeSettingsParam

EXIT_COMMANDS = {"/exit", "/quit", "exit", "quit"}


def require_realtime_url() -> None:
    """Require an explicit realtime WebSocket endpoint."""
    if not os.getenv("GIGACHAT_REALTIME_URL"):
        raise RuntimeError("Set GIGACHAT_REALTIME_URL to the protobuf-over-WebSocket realtime endpoint.")


def build_settings(
    voice_call_id: str,
    messages: List[RealtimeContextMessageParam],
    *,
    first_speaker: str,
) -> RealtimeSettingsParam:
    """Build text-only realtime settings for the current dialogue state."""
    return {
        "voice_call_id": voice_call_id,
        "mode": "GIGACHAT_SYNTHESIS",
        "output_modalities": "TEXT",
        "first_speaker": {"type": first_speaker},
        "gigachat": {
            "model": os.getenv("GIGACHAT_MODEL", "GigaChat"),
        },
        "context": {
            "messages": messages,
        },
    }


async def prompt_input(prompt: str) -> str:
    """Read console input without blocking the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, prompt)


async def read_model_response(connection: Any) -> str:
    """Print and collect model output until the current turn is finished."""
    chunks: List[str] = []

    async for event in connection:
        if isinstance(event, OutputTranscriptionEvent):
            text = event.text or ""
            print(text, end="", flush=True)
            chunks.append(text)
            if event.finish_reason:
                print()
                break

        elif isinstance(event, OutputAdditionalDataEvent):
            print()
            break

        elif isinstance(event, RealtimeErrorEvent):
            raise RuntimeError(event.message)

    return "".join(chunks)


async def main() -> None:
    """Connect to realtime and keep sending user turns from stdin."""
    load_dotenv()
    require_realtime_url()

    voice_call_id = str(uuid4())
    messages: List[RealtimeContextMessageParam] = [
        {
            "role": "system",
            "content": os.getenv("GIGACHAT_REALTIME_SYSTEM_PROMPT", "Answer briefly and clearly."),
        }
    ]

    async with GigaChat() as client:
        async with client.a_realtime.connect(
            settings=build_settings(voice_call_id, messages, first_speaker="user")
        ) as connection:
            while True:
                try:
                    user_text = (await prompt_input("user: ")).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if not user_text:
                    continue
                if user_text.lower() in EXIT_COMMANDS:
                    break

                messages.append({"role": "user", "content": user_text})
                await connection.session.send_settings(
                    build_settings(voice_call_id, messages, first_speaker="model")
                )

                print("assistant: ", end="", flush=True)
                assistant_text = await read_model_response(connection)
                if assistant_text:
                    messages.append({"role": "assistant", "content": assistant_text})


if __name__ == "__main__":
    asyncio.run(main())
