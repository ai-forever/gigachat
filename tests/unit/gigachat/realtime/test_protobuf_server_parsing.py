from typing import Any

import pytest

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
    RealtimeWarningEvent,
)
from gigachat.proto.gigavoice import voice_pb2
from gigachat.realtime._protobuf import duration_to_pb, parse_server_event, response_to_event

_PB2 = vars(voice_pb2)
_ADDITIONAL_DATA: Any = _PB2["AdditionalData"]
_ADULT: Any = _PB2["ADULT"]
_AUDIO: Any = _PB2["Audio"]
_CONTENT_FROM_MODEL: Any = _PB2["ContentFromModel"]
_EMOTION: Any = _PB2["Emotion"]
_ERROR: Any = _PB2["Error"]
_FEMALE: Any = _PB2["FEMALE"]
_FILE: Any = _PB2["File"]
_FUNCTION_CALL: Any = _PB2["FunctionCall"]
_FUNCTION_CALLING: Any = _PB2["FunctionCalling"]
_GIGACHAT_MODEL_INFO: Any = _PB2["GigaChatModelInfo"]
_GIGA_VOICE_RESPONSE: Any = _PB2["GigaVoiceResponse"]
_INPUT_FILES: Any = _PB2["InputFiles"]
_INPUT_TRANSCRIPTION: Any = _PB2["InputTranscription"]
_OUTPUT_TRANSCRIPTION: Any = _PB2["OutputTranscription"]
_PERSON_IDENTITY: Any = _PB2["PersonIdentity"]
_PLATFORM_FUNCTION_PROCESSING: Any = _PB2["PlatformFunctionProcessing"]
_USAGE: Any = _PB2["Usage"]
_WARNING: Any = _PB2["Warning"]


def _parse_response(response: Any) -> Any:
    return parse_server_event(response.SerializeToString())


def test_parse_output_audio_event() -> None:
    event = _parse_response(
        _GIGA_VOICE_RESPONSE(
            output=_CONTENT_FROM_MODEL(
                audio=_AUDIO(audio_chunk=b"pcm", audio_duration=duration_to_pb(1.25), is_final=True)
            )
        )
    )

    assert isinstance(event, OutputAudioEvent)
    assert event.audio_chunk == b"pcm"
    assert event.audio_duration == 1.25
    assert event.is_final is True


def test_parse_output_additional_data_event() -> None:
    event = _parse_response(
        _GIGA_VOICE_RESPONSE(
            output=_CONTENT_FROM_MODEL(
                additional_data=_ADDITIONAL_DATA(
                    usage=_USAGE(
                        prompt_tokens=1,
                        completion_tokens=2,
                        total_tokens=3,
                        precached_prompt_tokens=4,
                    ),
                    gigachat_model_info=_GIGACHAT_MODEL_INFO(name="GigaChat", version="latest"),
                    finish_reason="stop",
                )
            )
        )
    )

    assert isinstance(event, OutputAdditionalDataEvent)
    assert event.prompt_tokens == 1
    assert event.completion_tokens == 2
    assert event.total_tokens == 3
    assert event.precached_prompt_tokens == 4
    assert event.gigachat_model_info is not None
    assert event.gigachat_model_info.name == "GigaChat"
    assert event.finish_reason == "stop"


def test_parse_output_interrupted_event() -> None:
    event = _parse_response(_GIGA_VOICE_RESPONSE(output=_CONTENT_FROM_MODEL(interrupted=False)))

    assert isinstance(event, OutputInterruptedEvent)
    assert event.interrupted is False


def test_parse_function_call_event() -> None:
    event = _parse_response(
        _GIGA_VOICE_RESPONSE(
            function_call=_FUNCTION_CALLING(
                function_call=_FUNCTION_CALL(name="search", arguments='{"q":"hello"}'),
                timestamp=10,
            )
        )
    )

    assert isinstance(event, FunctionCallEvent)
    assert event.name == "search"
    assert event.arguments == '{"q":"hello"}'
    assert event.timestamp == 10


def test_parse_input_transcription_event() -> None:
    event = _parse_response(
        _GIGA_VOICE_RESPONSE(
            input_transcription=_INPUT_TRANSCRIPTION(
                text="hello",
                timestamp=11,
                unnormalized_text="helo",
                person_identity=_PERSON_IDENTITY(
                    age=_ADULT,
                    gender=_FEMALE,
                    age_score=0.8,
                    gender_score=0.9,
                ),
                prefetch=True,
                whisper=False,
                emotion=_EMOTION(positive=0.7, neutral=0.2, negative=0.1),
            )
        )
    )

    assert isinstance(event, InputTranscriptionEvent)
    assert event.text == "hello"
    assert event.timestamp == 11
    assert event.unnormalized_text == "helo"
    assert event.prefetch is True
    assert event.whisper is False
    assert event.person_identity is not None
    assert event.person_identity.age == "ADULT"
    assert event.person_identity.gender == "FEMALE"
    assert event.person_identity.age_score == pytest.approx(0.8)
    assert event.person_identity.gender_score == pytest.approx(0.9)
    assert event.emotion is not None
    assert event.emotion.positive == pytest.approx(0.7)


def test_parse_output_transcription_event() -> None:
    event = _parse_response(
        _GIGA_VOICE_RESPONSE(
            output_transcription=_OUTPUT_TRANSCRIPTION(
                text="answer",
                functions_state_id="state",
                finish_reason="stop",
                timestamp=12,
                stub_text="stub",
                inline_data={"mime": "text/plain"},
                silence_phrase=True,
            )
        )
    )

    assert isinstance(event, OutputTranscriptionEvent)
    assert event.text == "answer"
    assert event.functions_state_id == "state"
    assert event.finish_reason == "stop"
    assert event.timestamp == 12
    assert event.stub_text == "stub"
    assert event.inline_data == {"mime": "text/plain"}
    assert event.silence_phrase is True


def test_parse_error_event() -> None:
    event = _parse_response(_GIGA_VOICE_RESPONSE(error=_ERROR(status=400, message="bad request")))

    assert isinstance(event, RealtimeErrorEvent)
    assert event.status == 400
    assert event.message == "bad request"


def test_parse_warning_event() -> None:
    event = _parse_response(_GIGA_VOICE_RESPONSE(warning=_WARNING(message="slow input")))

    assert isinstance(event, RealtimeWarningEvent)
    assert event.message == "slow input"


def test_parse_input_files_event() -> None:
    event = _parse_response(_GIGA_VOICE_RESPONSE(input_files=_INPUT_FILES(files=[_FILE(id="file-id", type="audio")])))

    assert isinstance(event, InputFilesEvent)
    assert len(event.files) == 1
    assert event.files[0].id == "file-id"
    assert event.files[0].type == "audio"


def test_parse_platform_function_processing_event() -> None:
    event = _parse_response(
        _GIGA_VOICE_RESPONSE(
            platform_function_processing=_PLATFORM_FUNCTION_PROCESSING(name="profile", timestamp=13)
        )
    )

    assert isinstance(event, PlatformFunctionProcessingEvent)
    assert event.name == "profile"
    assert event.timestamp == 13


def test_response_to_event_rejects_empty_response() -> None:
    with pytest.raises(ValueError, match="Empty GigaVoiceResponse"):
        response_to_event(_GIGA_VOICE_RESPONSE())


def test_parse_server_event_rejects_invalid_protobuf() -> None:
    with pytest.raises(ValueError, match="Invalid realtime protobuf server event frame"):
        parse_server_event(b"not protobuf")
