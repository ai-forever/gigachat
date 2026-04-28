"""Run a text-only realtime conversation over protobuf WebSocket."""

import asyncio
import os
from uuid import uuid4

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models.realtime import OutputAdditionalDataEvent, OutputTranscriptionEvent, RealtimeErrorEvent
from gigachat.types.realtime import RealtimeSettingsParam


def require_realtime_url() -> None:
    """Require an explicit realtime WebSocket endpoint."""
    if not os.getenv("GIGACHAT_REALTIME_URL"):
        raise RuntimeError("Set GIGACHAT_REALTIME_URL to the protobuf-over-WebSocket realtime endpoint.")


def build_settings(prompt: str) -> RealtimeSettingsParam:
    """Build text-only realtime settings."""
    return {
        "voice_call_id": str(uuid4()),
        "mode": "GIGACHAT_SYNTHESIS",
        "output_modalities": "TEXT",
        "first_speaker": {"type": "model"},
        "gigachat": {
            "model": os.getenv("GIGACHAT_MODEL", "GigaChat"),
        },
        "context": {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        },
    }


async def main() -> None:
    """Connect to a realtime WebSocket endpoint and print text events."""
    load_dotenv()
    require_realtime_url()

    prompt = os.getenv("GIGACHAT_REALTIME_PROMPT", "Give a short overview of realtime SDK clients.")

    async with GigaChat() as client:
        async with client.a_realtime.connect(settings=build_settings(prompt)) as connection:
            async for event in connection:
                if isinstance(event, OutputTranscriptionEvent):
                    print(event.text or "", end="", flush=True)

                elif isinstance(event, OutputAdditionalDataEvent):
                    print()
                    print(f"finish_reason={event.finish_reason}")
                    break

                elif isinstance(event, RealtimeErrorEvent):
                    raise RuntimeError(event.message)


if __name__ == "__main__":
    asyncio.run(main())
