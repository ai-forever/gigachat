import json
from datetime import timedelta
from typing import Any, Dict, Mapping, Sequence, Union, cast

from google.protobuf import duration_pb2  # type: ignore[import-untyped]
from google.protobuf.message import DecodeError  # type: ignore[import-untyped]

from gigachat.models.realtime import RealtimeServerEvent, parse_realtime_event
from gigachat.proto.gigavoice import voice_pb2
from gigachat.realtime._base64 import validate_pcm16_chunk_duration
from gigachat.types.realtime import RealtimeClientEventParam, RealtimeSettingsParam

_PB2 = vars(voice_pb2)
_AGE_TYPE: Any = _PB2["AgeType"]
_ANY_EXAMPLE: Any = _PB2["AnyExample"]
_AUDIO_CHUNK_META: Any = _PB2["AudioChunkMeta"]
_AUDIO_CONTENT: Any = _PB2["AudioContent"]
_AUDIO_SETTINGS: Any = _PB2["AudioSettings"]
_CONTENT_FOR_SYNTHESIS: Any = _PB2["ContentForSynthesis"]
_CONTENT_FROM_CLIENT: Any = _PB2["ContentFromClient"]
_DISABLE_INTERRUPTION: Any = _PB2["DisableInterruption"]
_FILTER_SETTINGS: Any = _PB2["FilterSettings"]
_FIRST_SPEAKER: Any = _PB2["FirstSpeaker"]
_FUNCTION: Any = _PB2["Function"]
_FUNCTION_CALL: Any = _PB2["FunctionCall"]
_FUNCTION_RANKER: Any = _PB2["FunctionRanker"]
_FUNCTION_REGISTRY: Any = _PB2["FunctionRegistry"]
_FUNCTION_RESULT: Any = _PB2["FunctionResult"]
_GENDER_TYPE: Any = _PB2["GenderType"]
_GIGACHAT_SETTINGS: Any = _PB2["GigaChatSettings"]
_GIGA_VOICE_REQUEST: Any = _PB2["GigaVoiceRequest"]
_INITIAL_CONTEXT: Any = _PB2["InitialContext"]
_INPUT: Any = _PB2["Input"]
_MESSAGE: Any = _PB2["Message"]
_OUTPUT: Any = _PB2["Output"]
_PARAMS: Any = _PB2["Params"]
_SETTINGS: Any = _PB2["Settings"]
_STUB_SOUNDS: Any = _PB2["StubSounds"]
_TRIGGER_FUNCTION: Any = _PB2["TriggerFunction"]
_TRIGGER_GENERATION: Any = _PB2["TriggerGeneration"]
_GIGA_VOICE_RESPONSE: Any = _PB2["GigaVoiceResponse"]

MAX_CLIENT_EVENT_FRAME_SIZE = 4 * 1024 * 1024
DEFAULT_PCM16_SAMPLE_RATE = 16000
DEFAULT_PCM16_CHANNELS = 1
DEFAULT_MAX_AUDIO_CHUNK_SECONDS = 2.0


def client_event_to_request(
    event: RealtimeClientEventParam,
    *,
    validate_audio_chunks: bool = True,
    audio_sample_rate: int = DEFAULT_PCM16_SAMPLE_RATE,
    audio_channels: int = DEFAULT_PCM16_CHANNELS,
    max_audio_chunk_seconds: float = DEFAULT_MAX_AUDIO_CHUNK_SECONDS,
) -> Any:
    """Convert a realtime client event param to protobuf GigaVoiceRequest."""
    event_data = cast(Mapping[str, Any], event)
    event_type = event_data.get("type")
    request = _GIGA_VOICE_REQUEST()
    if event_type == "settings":
        request.settings.CopyFrom(settings_to_pb(cast(RealtimeSettingsParam, event_data["settings"])))
        return request
    if event_type == "input.audio_content":
        request.input.CopyFrom(
            _input_audio_content_event_to_pb(
                event_data,
                validate_audio_chunks,
                audio_sample_rate,
                audio_channels,
                max_audio_chunk_seconds,
            )
        )
        return request
    if event_type == "input.synthesis_content":
        request.input.CopyFrom(_input_synthesis_content_event_to_pb(event_data))
        return request
    if event_type == "function_result":
        request.function_result.CopyFrom(_function_result_event_to_pb(event_data))
        return request
    raise ValueError(f"Unsupported realtime client event type: {event_type!r}")


def serialize_client_event(
    event: RealtimeClientEventParam,
    *,
    max_frame_size: int = MAX_CLIENT_EVENT_FRAME_SIZE,
    validate_audio_chunks: bool = True,
    audio_sample_rate: int = DEFAULT_PCM16_SAMPLE_RATE,
    audio_channels: int = DEFAULT_PCM16_CHANNELS,
    max_audio_chunk_seconds: float = DEFAULT_MAX_AUDIO_CHUNK_SECONDS,
) -> bytes:
    """Serialize a realtime client event param to protobuf frame bytes."""
    request = client_event_to_request(
        event,
        validate_audio_chunks=validate_audio_chunks,
        audio_sample_rate=audio_sample_rate,
        audio_channels=audio_channels,
        max_audio_chunk_seconds=max_audio_chunk_seconds,
    )
    payload = cast(bytes, request.SerializeToString())
    _validate_frame_size(payload, max_frame_size=max_frame_size)
    return payload


def parse_server_event(data: bytes) -> RealtimeServerEvent:
    """Parse protobuf server frame bytes into a realtime event."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Realtime server event frame must be bytes")

    response = _GIGA_VOICE_RESPONSE()
    try:
        response.ParseFromString(bytes(data))
    except DecodeError as exc:
        raise ValueError("Invalid realtime protobuf server event frame") from exc
    return response_to_event(response)


def response_to_event(response: Any) -> RealtimeServerEvent:
    """Convert protobuf GigaVoiceResponse to a realtime event."""
    response_type = response.WhichOneof("response")
    if response_type is None:
        raise ValueError("Empty GigaVoiceResponse")

    if response_type == "output":
        return _output_to_event(response.output)
    if response_type == "function_call":
        return _function_calling_to_event(response.function_call)
    if response_type == "input_transcription":
        return _input_transcription_to_event(response.input_transcription)
    if response_type == "output_transcription":
        return _output_transcription_to_event(response.output_transcription)
    if response_type == "error":
        return parse_realtime_event(
            {"type": "error", "status": response.error.status, "message": response.error.message}
        )
    if response_type == "warning":
        return parse_realtime_event({"type": "warning", "message": response.warning.message})
    if response_type == "input_files":
        return _input_files_to_event(response.input_files)
    if response_type == "platform_function_processing":
        return parse_realtime_event(
            {
                "type": "platform_function_processing",
                "name": response.platform_function_processing.name,
                "timestamp": response.platform_function_processing.timestamp,
            }
        )
    raise ValueError(f"Unsupported GigaVoiceResponse oneof: {response_type!r}")


def settings_to_pb(settings: RealtimeSettingsParam) -> Any:
    """Convert realtime settings params to protobuf Settings."""
    if not settings.get("voice_call_id"):
        raise ValueError("Realtime settings require `voice_call_id`")

    pb = _SETTINGS()
    pb.voice_call_id = settings["voice_call_id"]

    _set_enum(pb, settings, "mode", _SETTINGS.Mode)
    _set_enum(pb, settings, "output_modalities", _SETTINGS.OutputModalities)
    _set_optional_scalars(
        pb,
        settings,
        (
            "disable_vad",
            "enable_transcribe_input",
            "enable_denoiser",
            "enable_prefetch",
            "enable_person_identity",
            "enable_whisper",
            "enable_emotion",
            "enable_transcribe_silence_phrases",
        ),
    )
    _extend_repeated(pb.flags, settings.get("flags"))

    gigachat = settings.get("gigachat")
    if gigachat is not None:
        pb.gigachat.CopyFrom(_gigachat_settings_to_pb(gigachat))

    audio = settings.get("audio")
    if audio is not None:
        pb.audio.CopyFrom(_audio_settings_to_pb(audio))

    context = settings.get("context")
    if context is not None:
        pb.context.CopyFrom(_initial_context_to_pb(context))

    first_speaker = settings.get("first_speaker")
    if first_speaker is not None:
        pb.first_speaker.CopyFrom(_first_speaker_to_pb(first_speaker))

    disable_interruption = settings.get("disable_interruption")
    if disable_interruption is not None:
        pb.disable_interruption.CopyFrom(_disable_interruption_to_pb(disable_interruption))

    return pb


def duration_to_pb(value: Union[int, float, timedelta]) -> Any:
    """Convert seconds or timedelta to protobuf Duration."""
    pb = duration_pb2.Duration()
    if isinstance(value, timedelta):
        pb.FromTimedelta(value)
        return pb

    seconds_float = float(value)
    seconds = int(seconds_float)
    nanos = int(round((seconds_float - seconds) * 1_000_000_000))
    if nanos == 1_000_000_000:
        seconds += 1
        nanos = 0
    pb.seconds = seconds
    pb.nanos = nanos
    return pb


def duration_from_pb(value: Any) -> float:
    """Convert protobuf Duration to seconds."""
    return cast(float, value.seconds + value.nanos / 1_000_000_000)


def enum_value(enum_cls: Any, value: str, *, field_name: str) -> int:
    """Return protobuf enum value by name."""
    try:
        return cast(int, enum_cls.Value(value))
    except ValueError as exc:
        raise ValueError(f"Invalid realtime `{field_name}` enum value: {value!r}") from exc


def json_string(value: Union[str, Mapping[str, Any], Sequence[Any]], *, field_name: str) -> str:
    """Return compact JSON string for schema-like protobuf string fields."""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping) or (isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray))):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    raise TypeError(f"Realtime `{field_name}` must be a string, mapping, or sequence")


def _output_to_event(output: Any) -> RealtimeServerEvent:
    output_type = output.WhichOneof("response")
    if output_type is None:
        raise ValueError("Empty GigaVoiceResponse.output")

    if output_type == "audio":
        return _output_audio_to_event(output.audio)
    if output_type == "additional_data":
        return _additional_data_to_event(output.additional_data)
    if output_type == "interrupted":
        return parse_realtime_event({"type": "output.interrupted", "interrupted": output.interrupted})
    raise ValueError(f"Unsupported ContentFromModel oneof: {output_type!r}")


def _output_audio_to_event(audio: Any) -> RealtimeServerEvent:
    data: Dict[str, Any] = {"type": "output.audio", "audio_chunk": audio.audio_chunk}
    if audio.HasField("audio_duration"):
        data["audio_duration"] = duration_from_pb(audio.audio_duration)
    if audio.HasField("is_final"):
        data["is_final"] = audio.is_final
    return parse_realtime_event(data)


def _additional_data_to_event(additional_data: Any) -> RealtimeServerEvent:
    data: Dict[str, Any] = {"type": "output.additional_data"}
    if additional_data.HasField("usage"):
        usage = additional_data.usage
        data.update(
            {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "precached_prompt_tokens": usage.precached_prompt_tokens,
            }
        )
    if additional_data.HasField("gigachat_model_info"):
        data["gigachat_model_info"] = {
            "name": additional_data.gigachat_model_info.name,
            "version": additional_data.gigachat_model_info.version,
        }
    if additional_data.finish_reason:
        data["finish_reason"] = additional_data.finish_reason
    return parse_realtime_event(data)


def _function_calling_to_event(function_calling: Any) -> RealtimeServerEvent:
    return parse_realtime_event(
        {
            "type": "function_call",
            "name": function_calling.function_call.name,
            "arguments": function_calling.function_call.arguments,
            "timestamp": function_calling.timestamp,
        }
    )


def _input_transcription_to_event(input_transcription: Any) -> RealtimeServerEvent:
    data: Dict[str, Any] = {
        "type": "input_transcription",
        "text": input_transcription.text,
        "timestamp": input_transcription.timestamp,
    }
    if input_transcription.HasField("unnormalized_text"):
        data["unnormalized_text"] = input_transcription.unnormalized_text
    if input_transcription.HasField("person_identity"):
        person_identity = input_transcription.person_identity
        data["person_identity"] = {
            "age": _enum_name(_AGE_TYPE, person_identity.age),
            "gender": _enum_name(_GENDER_TYPE, person_identity.gender),
            "age_score": person_identity.age_score,
            "gender_score": person_identity.gender_score,
        }
    if input_transcription.HasField("prefetch"):
        data["prefetch"] = input_transcription.prefetch
    if input_transcription.HasField("whisper"):
        data["whisper"] = input_transcription.whisper
    if input_transcription.HasField("emotion"):
        data["emotion"] = {
            "positive": input_transcription.emotion.positive,
            "neutral": input_transcription.emotion.neutral,
            "negative": input_transcription.emotion.negative,
        }
    return parse_realtime_event(data)


def _output_transcription_to_event(output_transcription: Any) -> RealtimeServerEvent:
    data: Dict[str, Any] = {
        "type": "output_transcription",
        "text": output_transcription.text,
        "functions_state_id": output_transcription.functions_state_id,
        "finish_reason": output_transcription.finish_reason,
        "timestamp": output_transcription.timestamp,
    }
    if output_transcription.HasField("stub_text"):
        data["stub_text"] = output_transcription.stub_text
    if output_transcription.inline_data:
        data["inline_data"] = dict(output_transcription.inline_data)
    if output_transcription.HasField("silence_phrase"):
        data["silence_phrase"] = output_transcription.silence_phrase
    return parse_realtime_event(data)


def _input_files_to_event(input_files: Any) -> RealtimeServerEvent:
    return parse_realtime_event(
        {
            "type": "input_files",
            "files": [{"id": file.id, "type": file.type} for file in input_files.files],
        }
    )


def _enum_name(enum_cls: Any, value: int) -> str:
    try:
        return cast(str, enum_cls.Name(value))
    except ValueError:
        return str(value)


def _input_audio_content_event_to_pb(
    event: Mapping[str, Any],
    validate_audio_chunks: bool,
    audio_sample_rate: int,
    audio_channels: int,
    max_audio_chunk_seconds: float,
) -> Any:
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

    input_pb = _CONTENT_FROM_CLIENT()
    audio_pb = _AUDIO_CONTENT()
    audio_pb.audio_chunk = audio_chunk
    _set_optional_scalars(audio_pb, event, ("speech_start", "speech_end"))

    meta = event.get("meta")
    if meta is not None:
        audio_pb.meta.CopyFrom(_audio_chunk_meta_to_pb(meta))

    input_pb.audio_content.CopyFrom(audio_pb)
    return input_pb


def _audio_chunk_meta_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _AUDIO_CHUNK_META()
    force_no_speech = data.get("force_no_speech")
    force_co_speech = data.get("force_co_speech")
    if force_no_speech is not None and force_co_speech is not None and force_no_speech != force_co_speech:
        raise ValueError("Realtime `meta.force_no_speech` and `meta.force_co_speech` values differ")
    if force_no_speech is not None:
        pb.force_no_speech = force_no_speech
    elif force_co_speech is not None:
        pb.force_no_speech = force_co_speech
    return pb


def _input_synthesis_content_event_to_pb(event: Mapping[str, Any]) -> Any:
    text = event.get("text")
    if not isinstance(text, str):
        raise TypeError("text must be str")

    input_pb = _CONTENT_FROM_CLIENT()
    content_pb = _CONTENT_FOR_SYNTHESIS()
    content_pb.text = text
    content_type = event.get("content_type")
    if content_type is not None:
        content_pb.content_type = _content_for_synthesis_type_value(content_type)
    _set_optional_scalars(content_pb, event, ("is_final",))
    input_pb.content_for_synthesis.CopyFrom(content_pb)
    return input_pb


def _content_for_synthesis_type_value(value: str) -> int:
    if not isinstance(value, str):
        raise TypeError("content_type must be str")
    return enum_value(_CONTENT_FOR_SYNTHESIS.ContentType, value.upper(), field_name="content_type")


def _function_result_event_to_pb(event: Mapping[str, Any]) -> Any:
    pb = _FUNCTION_RESULT()
    content = event.get("content")
    if content is None:
        raise ValueError("Realtime function result requires `content`")
    pb.content = json_string(content, field_name="content")
    _set_optional_scalars(pb, event, ("function_name",))
    return pb


def _gigachat_settings_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _GIGACHAT_SETTINGS()
    _set_optional_scalars(
        pb,
        data,
        (
            "model",
            "preset",
            "temperature",
            "top_p",
            "repetition_penalty",
            "update_interval",
            "profanity_check",
            "current_time",
        ),
    )
    _extend_repeated(pb.filter_stub_phrases, data.get("filter_stub_phrases"))

    filters_settings = data.get("filters_settings")
    if filters_settings is not None:
        for key, value in filters_settings.items():
            pb.filters_settings[key].CopyFrom(_filter_settings_to_pb(value))

    functions = data.get("functions")
    if functions is not None:
        for function in functions:
            pb.functions.append(_function_to_pb(function))

    function_registry = data.get("function_registry")
    if function_registry is not None:
        pb.function_registry.CopyFrom(_function_registry_to_pb(function_registry))

    function_ranker = data.get("function_ranker")
    if function_ranker is not None:
        pb.function_ranker.CopyFrom(_function_ranker_to_pb(function_ranker))

    return pb


def _audio_settings_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _AUDIO_SETTINGS()
    input_settings = data.get("input")
    if input_settings is not None:
        pb.input.CopyFrom(_input_settings_to_pb(input_settings))
    output_settings = data.get("output")
    if output_settings is not None:
        pb.output.CopyFrom(_output_settings_to_pb(output_settings))
    return pb


def _input_settings_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _INPUT()
    _set_optional_scalars(pb, data, ("model", "sample_rate"))
    _set_enum(pb, data, "audio_encoding", _INPUT.AudioEncoding)
    _extend_repeated(pb.silence_phrases, data.get("silence_phrases"))
    _extend_repeated(pb.stop_phrases, data.get("stop_phrases"))
    _extend_repeated(pb.ignore_phrases, data.get("ignore_phrases"))
    if data.get("silence_phrases_timeout") is not None:
        pb.silence_phrases_timeout.CopyFrom(duration_to_pb(data["silence_phrases_timeout"]))
    if data.get("silence_timeout") is not None:
        pb.silence_timeout.CopyFrom(duration_to_pb(data["silence_timeout"]))
    return pb


def _output_settings_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _OUTPUT()
    _set_optional_scalars(pb, data, ("voice",))
    _set_enum(pb, data, "audio_encoding", _OUTPUT.AudioEncoding)
    stub_sounds = data.get("stub_sounds")
    if stub_sounds is not None:
        pb.stub_sounds.CopyFrom(_stub_sounds_to_pb(stub_sounds))
    return pb


def _filter_settings_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _FILTER_SETTINGS()
    request_content = data.get("request_content")
    if request_content is not None:
        _set_optional_scalars(pb.request_content, request_content, ("neuro", "blacklist", "whitelist"))
    response_content = data.get("response_content")
    if response_content is not None:
        _set_optional_scalars(pb.response_content, response_content, ("blacklist",))
    return pb


def _function_to_pb(data: Mapping[str, Any]) -> Any:
    if not data.get("name"):
        raise ValueError("Realtime function requires `name`")

    pb = _FUNCTION()
    pb.name = data["name"]
    _set_optional_scalars(pb, data, ("description",))
    if data.get("parameters") is not None:
        pb.parameters = json_string(data["parameters"], field_name="parameters")
    if data.get("return_parameters") is not None:
        pb.return_parameters = json_string(data["return_parameters"], field_name="return_parameters")

    few_shot_examples = data.get("few_shot_examples")
    if few_shot_examples is not None:
        for example in few_shot_examples:
            pb.few_shot_examples.append(_any_example_to_pb(example))
    return pb


def _any_example_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _ANY_EXAMPLE()
    _set_optional_scalars(pb, data, ("request",))
    params = data.get("params")
    if isinstance(params, Mapping):
        pb.params.CopyFrom(_params_to_pb(params))
    return pb


def _params_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _PARAMS()
    pairs = data.get("pairs")
    if isinstance(pairs, Sequence) and not isinstance(pairs, (str, bytes, bytearray)):
        for pair in pairs:
            pair_pb = pb.pairs.add()
            pair_pb.key = str(pair["key"])
            pair_pb.value = str(pair["value"])
        return pb

    for key, value in data.items():
        pair_pb = pb.pairs.add()
        pair_pb.key = str(key)
        pair_pb.value = str(value)
    return pb


def _function_registry_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _FUNCTION_REGISTRY()
    _set_optional_scalars(pb, data, ("profile", "ab_flags"))
    _extend_repeated(pb.labels, data.get("labels"))
    return pb


def _function_ranker_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _FUNCTION_RANKER()
    enabled = data.get("enabled")
    enable = data.get("enable")
    if enabled is not None and enable is not None and enabled != enable:
        raise ValueError("Realtime `function_ranker.enable` and `function_ranker.enabled` values differ")
    if enabled is not None:
        pb.enabled = enabled
    elif enable is not None:
        pb.enabled = enable
    _set_optional_scalars(pb, data, ("top_n",))
    return pb


def _initial_context_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _INITIAL_CONTEXT()
    messages = data.get("messages")
    if messages is not None:
        for message in messages:
            pb.messages.append(_message_to_pb(message))
    return pb


def _message_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _MESSAGE()
    _set_optional_scalars(pb, data, ("role", "content", "function_name", "functions_state_id"))
    _extend_repeated(pb.attachments, data.get("attachments"))
    inline_data = data.get("inline_data")
    if inline_data is not None:
        pb.inline_data.update(inline_data)
    function_call = data.get("function_call")
    if function_call is not None:
        pb.function_call.CopyFrom(_function_call_to_pb(function_call))
    functions = data.get("functions")
    if functions is not None:
        for function in functions:
            pb.functions.append(_function_to_pb(function))
    return pb


def _function_call_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _FUNCTION_CALL()
    _set_optional_scalars(pb, data, ("name",))
    if data.get("arguments") is not None:
        pb.arguments = json_string(data["arguments"], field_name="arguments")
    return pb


def _first_speaker_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _FIRST_SPEAKER()
    _set_optional_scalars(pb, data, ("type", "lock_first_in"))
    return pb


def _disable_interruption_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _DISABLE_INTERRUPTION()
    functions = data.get("functions")
    if functions is not None:
        for function in functions:
            function_pb = pb.functions.add()
            _set_optional_scalars(function_pb, function, ("name", "on_execution", "after_result"))
    return pb


def _stub_sounds_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _STUB_SOUNDS()
    trigger_generation = data.get("trigger_generation")
    if trigger_generation is not None:
        pb.trigger_generation.CopyFrom(_trigger_generation_to_pb(trigger_generation))
    trigger_function = data.get("trigger_function")
    if trigger_function is not None:
        pb.trigger_function.CopyFrom(_trigger_function_to_pb(trigger_function))
    _extend_repeated(pb.sounds, data.get("sounds"))
    return pb


def _trigger_generation_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _TRIGGER_GENERATION()
    _set_optional_scalars(pb, data, ("enable",))
    if data.get("timeout") is not None:
        pb.timeout.CopyFrom(duration_to_pb(data["timeout"]))
    return pb


def _trigger_function_to_pb(data: Mapping[str, Any]) -> Any:
    pb = _TRIGGER_FUNCTION()
    _set_optional_scalars(pb, data, ("enable",))
    _set_enum(pb, data, "mode", _TRIGGER_FUNCTION.Mode)
    _extend_repeated(pb.function_names, data.get("function_names"))
    return pb


def _set_optional_scalars(pb: Any, data: Mapping[str, Any], fields: Sequence[str]) -> None:
    for field in fields:
        if field in data and data[field] is not None:
            setattr(pb, field, data[field])


def _set_enum(pb: Any, data: Mapping[str, Any], field: str, enum_cls: Any) -> None:
    if field in data and data[field] is not None:
        setattr(pb, field, enum_value(enum_cls, data[field], field_name=field))


def _extend_repeated(pb_repeated: Any, values: Any) -> None:
    if values is not None:
        pb_repeated.extend(values)


def _validate_frame_size(payload: bytes, *, max_frame_size: int) -> None:
    if max_frame_size <= 0:
        raise ValueError("max_frame_size must be positive")

    frame_size = len(payload)
    if frame_size > max_frame_size:
        raise ValueError(f"Realtime client event frame exceeds {max_frame_size} bytes: {frame_size} bytes")


__all__ = (
    "DEFAULT_MAX_AUDIO_CHUNK_SECONDS",
    "DEFAULT_PCM16_CHANNELS",
    "DEFAULT_PCM16_SAMPLE_RATE",
    "MAX_CLIENT_EVENT_FRAME_SIZE",
    "client_event_to_request",
    "duration_from_pb",
    "duration_to_pb",
    "enum_value",
    "json_string",
    "parse_server_event",
    "response_to_event",
    "serialize_client_event",
    "settings_to_pb",
)
