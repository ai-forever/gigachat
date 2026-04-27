import base64

from gigachat.models.realtime import (
    FunctionCallEvent,
    InputFilesEvent,
    InputTranscriptionEvent,
    OutputAdditionalDataEvent,
    OutputAudioEvent,
    OutputInterruptedEvent,
    OutputTranscriptionEvent,
    PlatformFunctionProcessingEvent,
    RealtimeErrorEvent,
    RealtimeUnknownEvent,
    RealtimeWarningEvent,
    parse_realtime_event,
)


def test_parse_output_audio_event_decodes_base64() -> None:
    event = parse_realtime_event(
        {
            "type": "output.audio",
            "audio_chunk": base64.b64encode(b"pcm").decode("ascii"),
            "audio_duration": 0.1,
            "is_final": True,
            "new_field": "kept",
        }
    )

    assert isinstance(event, OutputAudioEvent)
    assert event.audio_chunk == b"pcm"
    assert event.audio_duration == 0.1
    assert event.is_final is True
    assert event.model_extra == {"new_field": "kept"}


def test_parse_output_additional_data_event() -> None:
    event = parse_realtime_event(
        {
            "type": "output.additional_data",
            "prompt_tokens": 1,
            "completion_tokens": 2,
            "total_tokens": 3,
            "precached_prompt_tokens": 4,
            "gigachat_model_info": {"name": "GigaChat", "version": "latest"},
            "finish_reason": "stop",
        }
    )

    assert isinstance(event, OutputAdditionalDataEvent)
    assert event.prompt_tokens == 1
    assert event.gigachat_model_info is not None
    assert event.gigachat_model_info.name == "GigaChat"


def test_parse_output_interrupted_event() -> None:
    event = parse_realtime_event({"type": "output.interrupted"})

    assert isinstance(event, OutputInterruptedEvent)
    assert event.interrupted is True


def test_parse_function_call_event() -> None:
    event = parse_realtime_event({"type": "function_call", "name": "search", "arguments": "{}", "timestamp": 10})

    assert isinstance(event, FunctionCallEvent)
    assert event.name == "search"
    assert event.arguments == "{}"
    assert event.timestamp == 10


def test_parse_input_transcription_event() -> None:
    event = parse_realtime_event(
        {
            "type": "input_transcription",
            "text": "hello",
            "unnormalized_text": "helo",
            "prefetch": True,
            "person_identity": {"age": "adult", "gender": "unknown", "age_score": 0.8},
            "whisper": False,
            "emotion": {"positive": 0.7, "neutral": 0.2, "negative": 0.1},
            "timestamp": 11,
        }
    )

    assert isinstance(event, InputTranscriptionEvent)
    assert event.text == "hello"
    assert event.person_identity is not None
    assert event.person_identity.age_score == 0.8
    assert event.emotion is not None
    assert event.emotion.positive == 0.7


def test_parse_output_transcription_event() -> None:
    event = parse_realtime_event(
        {
            "type": "output_transcription",
            "text": "answer",
            "stub_text": "stub",
            "silence_phrase": False,
            "inline_data": {"mime": "text/plain"},
            "functions_state_id": "state",
            "finish_reason": "stop",
            "timestamp": 12,
        }
    )

    assert isinstance(event, OutputTranscriptionEvent)
    assert event.text == "answer"
    assert event.inline_data == {"mime": "text/plain"}


def test_parse_input_files_event() -> None:
    event = parse_realtime_event({"type": "input_files", "files": [{"id": "file-id", "type": "audio"}]})

    assert isinstance(event, InputFilesEvent)
    assert event.files[0].id == "file-id"


def test_parse_platform_function_processing_event() -> None:
    event = parse_realtime_event({"type": "platform_function_processing", "name": "profile", "timestamp": 13})

    assert isinstance(event, PlatformFunctionProcessingEvent)
    assert event.name == "profile"


def test_parse_error_event() -> None:
    event = parse_realtime_event({"type": "error", "status": 400, "status_code": 400, "message": "bad request"})

    assert isinstance(event, RealtimeErrorEvent)
    assert event.status == 400
    assert event.message == "bad request"


def test_parse_warning_event() -> None:
    event = parse_realtime_event({"type": "warning", "message": "slow input"})

    assert isinstance(event, RealtimeWarningEvent)
    assert event.message == "slow input"


def test_parse_unknown_event_preserves_fields() -> None:
    event = parse_realtime_event({"type": "new_event", "payload": {"x": 1}})

    assert isinstance(event, RealtimeUnknownEvent)
    assert event.type == "new_event"
    assert event.model_extra == {"payload": {"x": 1}}


def test_parse_missing_type_returns_unknown_event() -> None:
    event = parse_realtime_event({"payload": {"x": 1}})

    assert isinstance(event, RealtimeUnknownEvent)
    assert event.type == "unknown"
    assert event.model_extra == {"payload": {"x": 1}}


def test_parse_legacy_output_audio_event() -> None:
    event = parse_realtime_event({"output": {"audio": {"audio_chunk": base64.b64encode(b"pcm").decode("ascii")}}})

    assert isinstance(event, OutputAudioEvent)
    assert event.audio_chunk == b"pcm"


def test_parse_legacy_output_interrupted_bool_event() -> None:
    event = parse_realtime_event({"output": {"interrupted": False}})

    assert isinstance(event, OutputInterruptedEvent)
    assert event.interrupted is False
