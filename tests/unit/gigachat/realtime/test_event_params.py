from typing import get_args

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
        "RECOGNIZE_GIGACHAT_SYNTHESIS",
        "RECOGNIZE_SYNTHESIS",
        "GIGACHAT_SYNTHESIS",
    )
    assert get_args(RealtimeAudioEncoding) == ("PCM_S16LE", "OPUS", "PCM_ALAW")


def test_realtime_settings_required_keys() -> None:
    assert RealtimeSettingsParam.__required_keys__ == frozenset({"voice_call_id"})
    assert {"mode", "audio", "context", "flags"}.issubset(RealtimeSettingsParam.__optional_keys__)


def test_realtime_input_audio_content_required_keys() -> None:
    assert RealtimeInputAudioContentEventParam.__required_keys__ == frozenset({"type", "audio_chunk"})
    assert {"speech_start", "speech_end", "meta"}.issubset(RealtimeInputAudioContentEventParam.__optional_keys__)


def test_realtime_function_result_required_keys() -> None:
    assert RealtimeFunctionResultEventParam.__required_keys__ == frozenset({"type", "content", "function_name"})


def test_realtime_client_event_union() -> None:
    assert len(get_args(RealtimeClientEventParam)) == 4
