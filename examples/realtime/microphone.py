"""Stream microphone audio over protobuf WebSocket realtime."""

import asyncio
import os
from contextlib import suppress
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models.realtime import (
    InputTranscriptionEvent,
    OutputAdditionalDataEvent,
    OutputAudioEvent,
    OutputInterruptedEvent,
    OutputTranscriptionEvent,
    RealtimeErrorEvent,
)
from gigachat.realtime import RealtimeMicrophone, RealtimeSpeaker
from gigachat.types.realtime import RealtimeSettingsParam

SAMPLE_RATE = 24000


def require_realtime_url() -> None:
    """Require an explicit realtime WebSocket endpoint."""
    if not os.getenv("GIGACHAT_REALTIME_URL"):
        raise RuntimeError("Set GIGACHAT_REALTIME_URL to the protobuf-over-WebSocket realtime endpoint.")


def build_settings() -> RealtimeSettingsParam:
    """Build realtime settings for microphone input and speaker output."""
    return {
        "voice_call_id": str(uuid4()),
        "mode": "RECOGNIZE_GIGACHAT_SYNTHESIS",
        "output_modalities": "AUDIO_TEXT",
        "first_speaker": {"type": "model"},
        "enable_transcribe_input": True,
        "gigachat": {
            "model": os.getenv("GIGACHAT_MODEL", "GigaChat"),
        },
        "audio": {
            "input": {
                "audio_encoding": "PCM_S16LE",
                "sample_rate": SAMPLE_RATE,
            },
            "output": {
                "audio_encoding": "PCM_S16LE",
                "voice": os.getenv("GIGACHAT_REALTIME_VOICE", "Mar_24000"),
            },
        },
        "context": {
            "messages": [
                {
                    "role": "system",
                    "content": "Ты гигачат, голосовой ассистент, ты вежлив",
                }
            ]
        },
    }


async def send_microphone_audio(connection: Any, microphone: RealtimeMicrophone) -> None:
    """Send microphone PCM chunks to realtime input."""
    speech_start = True
    async for chunk in microphone:
        await connection.input_audio.send(chunk, speech_start=speech_start)
        speech_start = False


async def main() -> None:
    """Connect to realtime, stream microphone input, and play model audio."""
    load_dotenv()
    require_realtime_url()

    async with GigaChat() as client:
        async with client.a_realtime.connect(settings=build_settings()) as connection:
            async with RealtimeMicrophone(sample_rate=SAMPLE_RATE) as microphone:
                async with RealtimeSpeaker(sample_rate=SAMPLE_RATE) as speaker:
                    microphone_task = asyncio.create_task(send_microphone_audio(connection, microphone))
                    try:
                        async for event in connection:
                            if isinstance(event, InputTranscriptionEvent):
                                print(f"\nuser: {event.text}")

                            elif isinstance(event, OutputTranscriptionEvent):
                                print(event.text or "", end="", flush=True)

                            elif isinstance(event, OutputAudioEvent):
                                await speaker.write(event.audio_chunk)

                            elif isinstance(event, OutputInterruptedEvent):
                                speaker.stop()

                            elif isinstance(event, OutputAdditionalDataEvent):
                                print()
                                print(f"finish_reason={event.finish_reason}")
                                break

                            elif isinstance(event, RealtimeErrorEvent):
                                raise RuntimeError(event.message)
                    finally:
                        microphone.close()
                        with suppress(Exception):
                            await connection.input_audio.send(b"", speech_end=True)
                        microphone_task.cancel()
                        with suppress(asyncio.CancelledError):
                            await microphone_task


if __name__ == "__main__":
    asyncio.run(main())
