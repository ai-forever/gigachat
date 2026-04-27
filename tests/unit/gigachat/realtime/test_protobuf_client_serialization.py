from datetime import timedelta
from typing import Any, cast

import pytest

from gigachat.proto.gigavoice import voice_pb2
from gigachat.realtime._protobuf import duration_to_pb, enum_value, json_string, settings_to_pb
from gigachat.types.realtime import RealtimeSettingsParam

_PB2 = vars(voice_pb2)
_INPUT = _PB2["Input"]
_OUTPUT = _PB2["Output"]
_SETTINGS = _PB2["Settings"]
_TRIGGER_FUNCTION = _PB2["TriggerFunction"]


def test_settings_to_pb_minimal() -> None:
    pb = settings_to_pb({"voice_call_id": "call-id"})

    assert pb.voice_call_id == "call-id"
    assert not pb.HasField("mode")
    assert not pb.HasField("audio")


def test_settings_to_pb_full() -> None:
    pb = settings_to_pb(
        {
            "voice_call_id": "call-id",
            "mode": "RECOGNIZE_SYNTHESIS",
            "output_modalities": "AUDIO_TEXT",
            "disable_vad": True,
            "enable_transcribe_input": True,
            "flags": ["beta"],
            "first_speaker": {"type": "model", "lock_first_in": True},
            "disable_interruption": {"functions": [{"name": "search", "on_execution": True, "after_result": False}]},
            "audio": {
                "input": {
                    "model": "asr",
                    "audio_encoding": "PCM_S16LE",
                    "sample_rate": 16000,
                    "silence_phrases": ["..."],
                    "silence_phrases_timeout": 1.5,
                    "silence_timeout": timedelta(milliseconds=250),
                    "stop_phrases": ["stop"],
                    "ignore_phrases": ["ignore"],
                },
                "output": {
                    "voice": "Nec_24000",
                    "audio_encoding": "OPUS",
                    "stub_sounds": {
                        "trigger_generation": {"enable": True, "timeout": 0.25},
                        "trigger_function": {
                            "enable": True,
                            "mode": "WHITELIST",
                            "function_names": ["search"],
                        },
                        "sounds": ["typing"],
                    },
                },
            },
            "gigachat": {
                "model": "GigaChat",
                "preset": "voice",
                "temperature": 0.2,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
                "update_interval": 0.5,
                "profanity_check": False,
                "filters_settings": {
                    "default": {
                        "request_content": {"neuro": True, "blacklist": False, "whitelist": True},
                        "response_content": {"blacklist": True},
                    }
                },
                "functions": [
                    {
                        "name": "search",
                        "description": "Search",
                        "parameters": {"type": "object"},
                        "return_parameters": {"type": "object"},
                        "few_shot_examples": [{"request": "weather", "params": {"city": "Moscow"}}],
                    }
                ],
                "function_registry": {"profile": "assistant", "labels": ["public"], "ab_flags": "{}"},
                "function_ranker": {"enabled": True, "top_n": 3},
                "filter_stub_phrases": ["stub"],
                "current_time": 1700000000,
            },
            "context": {
                "messages": [
                    {
                        "role": "user",
                        "content": "hello",
                        "function_call": {"name": "search", "arguments": {"q": "hello"}},
                        "function_name": "search",
                        "functions_state_id": "state-id",
                        "attachments": ["file-id"],
                        "inline_data": {"source": "{}"},
                        "functions": [{"name": "search", "parameters": "{}"}],
                    }
                ]
            },
            "enable_denoiser": True,
            "enable_prefetch": True,
            "enable_person_identity": True,
            "enable_whisper": True,
            "enable_emotion": True,
            "enable_transcribe_silence_phrases": True,
        }
    )

    assert pb.mode == _SETTINGS.RECOGNIZE_SYNTHESIS
    assert pb.output_modalities == _SETTINGS.AUDIO_TEXT
    assert pb.disable_vad is True
    assert pb.enable_transcribe_input is True
    assert list(pb.flags) == ["beta"]
    assert pb.first_speaker.type == "model"
    assert pb.disable_interruption.functions[0].name == "search"
    assert pb.audio.input.model == "asr"
    assert pb.audio.input.audio_encoding == _INPUT.PCM_S16LE
    assert pb.audio.input.silence_phrases_timeout.seconds == 1
    assert pb.audio.input.silence_phrases_timeout.nanos == 500_000_000
    assert pb.audio.input.silence_timeout.nanos == 250_000_000
    assert pb.audio.output.audio_encoding == _OUTPUT.OPUS
    assert pb.audio.output.stub_sounds.trigger_generation.timeout.nanos == 250_000_000
    assert pb.audio.output.stub_sounds.trigger_function.mode == _TRIGGER_FUNCTION.WHITELIST
    assert pb.gigachat.model == "GigaChat"
    assert pb.gigachat.preset == "voice"
    assert pb.gigachat.filters_settings["default"].request_content.neuro is True
    assert pb.gigachat.functions[0].parameters == '{"type":"object"}'
    assert pb.gigachat.functions[0].return_parameters == '{"type":"object"}'
    assert pb.gigachat.functions[0].few_shot_examples[0].params.pairs[0].key == "city"
    assert pb.gigachat.function_registry.labels == ["public"]
    assert pb.gigachat.function_ranker.enabled is True
    assert pb.gigachat.function_ranker.top_n == 3
    assert pb.context.messages[0].function_call.arguments == '{"q":"hello"}'
    assert pb.context.messages[0].functions[0].name == "search"
    assert pb.enable_transcribe_silence_phrases is True


def test_duration_to_pb_converts_seconds_and_timedelta() -> None:
    assert duration_to_pb(2).seconds == 2
    assert duration_to_pb(1.25).nanos == 250_000_000
    assert duration_to_pb(timedelta(milliseconds=125)).nanos == 125_000_000


def test_function_ranker_enable_alias() -> None:
    pb = settings_to_pb({"voice_call_id": "call-id", "gigachat": {"function_ranker": {"enable": True}}})

    assert pb.gigachat.function_ranker.enabled is True


def test_function_ranker_enable_alias_conflict_raises() -> None:
    with pytest.raises(ValueError, match="values differ"):
        settings_to_pb(
            {
                "voice_call_id": "call-id",
                "gigachat": {"function_ranker": {"enable": True, "enabled": False}},
            }
        )


def test_settings_to_pb_requires_voice_call_id() -> None:
    with pytest.raises(ValueError, match="voice_call_id"):
        settings_to_pb(cast(RealtimeSettingsParam, cast(Any, {})))


def test_enum_value_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="mode"):
        enum_value(_SETTINGS.Mode, "UNKNOWN", field_name="mode")


def test_json_string_accepts_string_mapping_and_sequence() -> None:
    assert json_string("{}", field_name="parameters") == "{}"
    assert json_string({"type": "object"}, field_name="parameters") == '{"type":"object"}'
    assert json_string([{"name": "x"}], field_name="parameters") == '[{"name":"x"}]'
