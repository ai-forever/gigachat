import json
from typing import Any, Dict, Mapping

from gigachat.realtime._base64 import encode_audio, validate_pcm16_chunk_duration
from gigachat.types.realtime import RealtimeClientEventParam

MAX_CLIENT_EVENT_FRAME_SIZE = 4 * 1024 * 1024
DEFAULT_PCM16_SAMPLE_RATE = 16000
DEFAULT_PCM16_CHANNELS = 1
DEFAULT_MAX_AUDIO_CHUNK_SECONDS = 2.0


def serialize_client_event(
    event: RealtimeClientEventParam,
    *,
    max_frame_size: int = MAX_CLIENT_EVENT_FRAME_SIZE,
    validate_audio_chunks: bool = True,
    audio_sample_rate: int = DEFAULT_PCM16_SAMPLE_RATE,
    audio_channels: int = DEFAULT_PCM16_CHANNELS,
    max_audio_chunk_seconds: float = DEFAULT_MAX_AUDIO_CHUNK_SECONDS,
) -> str:
    json_data = _serialize_event_data(
        event, validate_audio_chunks, audio_sample_rate, audio_channels, max_audio_chunk_seconds
    )
    payload = json.dumps(json_data, ensure_ascii=False, separators=(",", ":"))
    _validate_frame_size(payload, max_frame_size=max_frame_size)
    return payload


def _serialize_event_data(
    event: Mapping[str, Any],
    validate_audio_chunks: bool,
    audio_sample_rate: int,
    audio_channels: int,
    max_audio_chunk_seconds: float,
) -> Dict[str, Any]:
    event_type = event.get("type")
    if event_type == "input.audio_content":
        return _serialize_input_audio_content_event(
            event,
            validate_audio_chunks,
            audio_sample_rate,
            audio_channels,
            max_audio_chunk_seconds,
        )
    if event_type == "function_result":
        return _serialize_function_result_event(event)
    return dict(event)


def _serialize_input_audio_content_event(
    event: Mapping[str, Any],
    validate_audio_chunks: bool,
    audio_sample_rate: int,
    audio_channels: int,
    max_audio_chunk_seconds: float,
) -> Dict[str, Any]:
    audio_chunk = event.get("audio_chunk")
    if not isinstance(audio_chunk, bytes):
        raise TypeError("audio_chunk must be bytes")

    if validate_audio_chunks:
        validate_pcm16_chunk_duration(
            audio_chunk,
            sample_rate=audio_sample_rate,
            channels=audio_channels,
            max_seconds=max_audio_chunk_seconds,
        )

    json_data = dict(event)
    json_data["audio_chunk"] = encode_audio(audio_chunk)
    return json_data


def _serialize_function_result_event(event: Mapping[str, Any]) -> Dict[str, Any]:
    json_data = dict(event)
    content = json_data.get("content")
    if isinstance(content, (dict, list)):
        json_data["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    return json_data


def _validate_frame_size(payload: str, *, max_frame_size: int) -> None:
    if max_frame_size <= 0:
        raise ValueError("max_frame_size must be positive")

    frame_size = len(payload.encode("utf-8"))
    if frame_size > max_frame_size:
        raise ValueError(f"Realtime client event frame exceeds {max_frame_size} bytes: {frame_size} bytes")


__all__ = (
    "DEFAULT_MAX_AUDIO_CHUNK_SECONDS",
    "DEFAULT_PCM16_CHANNELS",
    "DEFAULT_PCM16_SAMPLE_RATE",
    "MAX_CLIENT_EVENT_FRAME_SIZE",
    "serialize_client_event",
)
