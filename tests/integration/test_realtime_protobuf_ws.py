"""Integration smoke test for realtime protobuf-over-WebSocket backend."""

import asyncio
import os
from typing import Any, Optional
from uuid import uuid4

import pytest

from gigachat import GigaChat
from gigachat.models.realtime import RealtimeServerEvent
from gigachat.types.realtime import RealtimeSettingsParam

pytestmark = pytest.mark.integration

_SAMPLE_RATE = 16000


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}


def _require_realtime_backend_env() -> None:
    if not os.getenv("GIGACHAT_REALTIME_URL"):
        pytest.skip("GIGACHAT_REALTIME_URL environment variable not set")

    if os.getenv("GIGACHAT_ACCESS_TOKEN"):
        return
    if os.getenv("GIGACHAT_CREDENTIALS"):
        return
    if os.getenv("GIGACHAT_USER") and os.getenv("GIGACHAT_PASSWORD"):
        return

    pytest.skip("GIGACHAT_CREDENTIALS, GIGACHAT_ACCESS_TOKEN, or GIGACHAT_USER/GIGACHAT_PASSWORD not set")


def _smoke_timeout() -> float:
    return float(os.getenv("GIGACHAT_REALTIME_SMOKE_TIMEOUT", "5"))


def _build_smoke_settings() -> RealtimeSettingsParam:
    if _env_flag("GIGACHAT_REALTIME_SEND_SILENCE"):
        return {
            "voice_call_id": str(uuid4()),
            "mode": "RECOGNIZE_GIGACHAT_SYNTHESIS",
            "output_modalities": "AUDIO_TEXT",
            "first_speaker": {"type": "user"},
            "enable_transcribe_input": True,
            "gigachat": {
                "model": os.getenv("GIGACHAT_MODEL", "GigaChat"),
            },
            "audio": {
                "input": {
                    "audio_encoding": "PCM_S16LE",
                    "sample_rate": _SAMPLE_RATE,
                },
                "output": {
                    "audio_encoding": "PCM_S16LE",
                    "voice": os.getenv("GIGACHAT_REALTIME_VOICE", "Bys_24000"),
                },
            },
            "context": {"messages": [{"role": "system", "content": "Answer briefly."}]},
        }

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
                    "content": os.getenv("GIGACHAT_REALTIME_PROMPT", "Say ok in one short sentence."),
                }
            ]
        },
    }


async def _send_optional_silence(connection: Any) -> None:
    if not _env_flag("GIGACHAT_REALTIME_SEND_SILENCE"):
        return

    chunk_ms = int(os.getenv("GIGACHAT_REALTIME_SILENCE_MS", "100"))
    chunk_size = int(_SAMPLE_RATE * 2 * chunk_ms / 1000)
    await connection.input_audio.send(b"\x00" * chunk_size, speech_start=True, speech_end=True)


async def _recv_optional_event(connection: Any, timeout: float) -> Optional[RealtimeServerEvent]:
    try:
        return await asyncio.wait_for(connection.recv(), timeout=timeout)
    except asyncio.TimeoutError:
        return None


async def test_realtime_protobuf_websocket_smoke() -> None:
    """Open realtime WebSocket, send protobuf settings, and parse an optional protobuf response."""
    _require_realtime_backend_env()

    timeout = _smoke_timeout()
    async with GigaChat() as client:
        async with client.a_realtime.connect(
            settings=_build_smoke_settings(),
            websocket_connection_options={"open_timeout": timeout, "close_timeout": 1},
        ) as connection:
            await _send_optional_silence(connection)
            event = await _recv_optional_event(connection, timeout)

    if event is not None and event.type == "error":
        message = getattr(event, "message", "Realtime backend returned an error event")
        status = getattr(event, "status", None)
        pytest.fail(f"Realtime backend returned error event: status={status!r}, message={message!r}")
