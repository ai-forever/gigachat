import base64
import json
from typing import get_args

import pytest

from gigachat.realtime._events import serialize_client_event
from gigachat.types.realtime import (
    RealtimeAudioEncoding,
    RealtimeClientEventParam,
    RealtimeFunctionResultEventParam,
    RealtimeInputAudioContentEventParam,
    RealtimeMode,
    RealtimeSettingsParam,
)


def test_realtime_literal_aliases() -> None:
    assert get_args(RealtimeMode) == (
        "MODE_UNSPECIFIED",
        "RECOGNIZE_GIGACHAT_SYNTHESIS",
        "GIGACHAT_SYNTHESIS",
        "GIGACHAT",
        "RECOGNIZE_SYNTHESIS",
    )
    assert get_args(RealtimeAudioEncoding) == ("AUDIO_ENCODING_UNSPECIFIED", "PCM_S16LE", "OPUS", "PCM_ALAW")


def test_realtime_settings_required_keys() -> None:
    assert RealtimeSettingsParam.__required_keys__ == frozenset({"voice_call_id"})
    assert {"mode", "audio", "context", "flags"}.issubset(RealtimeSettingsParam.__optional_keys__)


def test_realtime_input_audio_content_required_keys() -> None:
    assert RealtimeInputAudioContentEventParam.__required_keys__ == frozenset({"type", "audio_chunk"})
    assert {"speech_start", "speech_end", "meta"}.issubset(RealtimeInputAudioContentEventParam.__optional_keys__)


def test_realtime_function_result_required_keys() -> None:
    assert RealtimeFunctionResultEventParam.__required_keys__ == frozenset({"type", "content"})
    assert "function_name" in RealtimeFunctionResultEventParam.__optional_keys__


def test_realtime_client_event_union() -> None:
    assert len(get_args(RealtimeClientEventParam)) == 4


def test_serialize_settings_event() -> None:
    payload = serialize_client_event(
        {
            "type": "settings",
            "settings": {
                "voice_call_id": "call-id",
                "mode": "RECOGNIZE_GIGACHAT_SYNTHESIS",
                "audio": {"input": {"audio_encoding": "PCM_S16LE", "sample_rate": 16000}},
            },
        }
    )

    assert json.loads(payload) == {
        "type": "settings",
        "settings": {
            "voice_call_id": "call-id",
            "mode": "RECOGNIZE_GIGACHAT_SYNTHESIS",
            "audio": {"input": {"audio_encoding": "PCM_S16LE", "sample_rate": 16000}},
        },
    }


def test_serialize_audio_event_encodes_base64() -> None:
    event: RealtimeInputAudioContentEventParam = {
        "type": "input.audio_content",
        "audio_chunk": b"pcm",
        "speech_start": True,
        "meta": {"force_co_speech": False},
    }

    payload = serialize_client_event(event)

    assert json.loads(payload) == {
        "type": "input.audio_content",
        "audio_chunk": base64.b64encode(b"pcm").decode("ascii"),
        "speech_start": True,
        "meta": {"force_co_speech": False},
    }
    assert event["audio_chunk"] == b"pcm"


def test_serialize_event_validates_frame_size() -> None:
    with pytest.raises(ValueError, match="frame exceeds 10 bytes"):
        serialize_client_event({"type": "settings", "settings": {"voice_call_id": "call-id"}}, max_frame_size=10)


def test_serialize_audio_event_validates_pcm_duration() -> None:
    with pytest.raises(ValueError, match="exceeds 2 seconds"):
        serialize_client_event({"type": "input.audio_content", "audio_chunk": b"\x00" * 64002})


def test_serialize_audio_event_can_skip_pcm_duration_validation() -> None:
    payload = serialize_client_event(
        {"type": "input.audio_content", "audio_chunk": b"\x00" * 64002},
        validate_audio_chunks=False,
    )

    assert json.loads(payload)["audio_chunk"] == base64.b64encode(b"\x00" * 64002).decode("ascii")


def test_serialize_function_result_event_converts_mapping_content_to_json_string() -> None:
    payload = serialize_client_event(
        {
            "type": "function_result",
            "function_name": "search",
            "content": {"items": [{"title": "ГигаЧат"}]},
        }
    )

    data = json.loads(payload)
    assert data == {
        "type": "function_result",
        "function_name": "search",
        "content": '{"items":[{"title":"ГигаЧат"}]}',
    }
    assert json.loads(data["content"]) == {"items": [{"title": "ГигаЧат"}]}
