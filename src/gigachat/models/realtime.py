import base64
from typing import Any, Dict, List, Mapping, Optional, Type, Union

from pydantic import BaseModel, ConfigDict, field_validator
from typing_extensions import Literal


class RealtimeServerEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str


class GigaChatModelInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    version: Optional[str] = None


class OutputAudioEvent(RealtimeServerEvent):
    type: Literal["output.audio"]
    audio_chunk: bytes
    audio_duration: Optional[Union[float, str]] = None
    is_final: Optional[bool] = None

    @field_validator("audio_chunk", mode="before")
    @classmethod
    def _decode_audio_chunk(cls, value: object) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return base64.b64decode(value)
        raise TypeError("audio_chunk must be base64 string or bytes")


class OutputAdditionalDataEvent(RealtimeServerEvent):
    type: Literal["output.additional_data"]
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    precached_prompt_tokens: Optional[int] = None
    gigachat_model_info: Optional[GigaChatModelInfo] = None
    finish_reason: Optional[str] = None


class OutputInterruptedEvent(RealtimeServerEvent):
    type: Literal["output.interrupted"]
    interrupted: bool = True


class FunctionCallEvent(RealtimeServerEvent):
    type: Literal["function_call"]
    name: str
    arguments: str
    timestamp: Optional[int] = None


class PersonIdentity(BaseModel):
    model_config = ConfigDict(extra="allow")

    age: Optional[str] = None
    gender: Optional[str] = None
    age_score: Optional[float] = None
    gender_score: Optional[float] = None


class Emotion(BaseModel):
    model_config = ConfigDict(extra="allow")

    positive: Optional[float] = None
    neutral: Optional[float] = None
    negative: Optional[float] = None


class InputTranscriptionEvent(RealtimeServerEvent):
    type: Literal["input_transcription"]
    text: str
    unnormalized_text: Optional[str] = None
    prefetch: Optional[bool] = None
    person_identity: Optional[PersonIdentity] = None
    whisper: Optional[bool] = None
    emotion: Optional[Emotion] = None
    timestamp: Optional[int] = None


class OutputTranscriptionEvent(RealtimeServerEvent):
    type: Literal["output_transcription"]
    text: Optional[str] = None
    stub_text: Optional[str] = None
    silence_phrase: Optional[bool] = None
    inline_data: Optional[Dict[str, str]] = None
    functions_state_id: Optional[str] = None
    finish_reason: Optional[str] = None
    timestamp: Optional[int] = None


class InputFileInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    type: str


class InputFilesEvent(RealtimeServerEvent):
    type: Literal["input_files"]
    files: List[InputFileInfo]


class PlatformFunctionProcessingEvent(RealtimeServerEvent):
    type: Literal["platform_function_processing"]
    name: str
    timestamp: Optional[int] = None


class RealtimeErrorEvent(RealtimeServerEvent):
    type: Literal["error"]
    status: Optional[int] = None
    status_code: Optional[int] = None
    message: str


class RealtimeWarningEvent(RealtimeServerEvent):
    type: Literal["warning"]
    message: str


class RealtimeUnknownEvent(RealtimeServerEvent):
    type: str


RealtimeServerEventType = Union[
    OutputAudioEvent,
    OutputAdditionalDataEvent,
    OutputInterruptedEvent,
    FunctionCallEvent,
    InputTranscriptionEvent,
    OutputTranscriptionEvent,
    InputFilesEvent,
    PlatformFunctionProcessingEvent,
    RealtimeErrorEvent,
    RealtimeWarningEvent,
    RealtimeUnknownEvent,
]

_EVENT_MODELS: Dict[str, Type[RealtimeServerEvent]] = {
    "output.audio": OutputAudioEvent,
    "output.additional_data": OutputAdditionalDataEvent,
    "output.interrupted": OutputInterruptedEvent,
    "function_call": FunctionCallEvent,
    "input_transcription": InputTranscriptionEvent,
    "output_transcription": OutputTranscriptionEvent,
    "input_files": InputFilesEvent,
    "platform_function_processing": PlatformFunctionProcessingEvent,
    "error": RealtimeErrorEvent,
    "warning": RealtimeWarningEvent,
}


def _normalize_legacy_event(data: Mapping[str, Any]) -> Dict[str, Any]:
    if "type" in data:
        return dict(data)

    output_event = _normalize_legacy_output_event(data)
    if output_event is not None:
        return output_event

    direct_event = _normalize_legacy_direct_event(data)
    if direct_event is not None:
        return direct_event

    return {"type": "unknown", **data}


def _normalize_legacy_output_event(data: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    output = data.get("output")
    if not isinstance(output, Mapping):
        return None

    for legacy_key, event_type in (
        ("audio", "output.audio"),
        ("additional_data", "output.additional_data"),
    ):
        payload = output.get(legacy_key)
        if isinstance(payload, Mapping):
            return {"type": event_type, **payload}

    interrupted = output.get("interrupted")
    if isinstance(interrupted, Mapping):
        return {"type": "output.interrupted", **interrupted}
    if isinstance(interrupted, bool):
        return {"type": "output.interrupted", "interrupted": interrupted}

    return None


def _normalize_legacy_direct_event(data: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    for legacy_key, event_type in (
        ("function_call", "function_call"),
        ("input_transcription", "input_transcription"),
        ("output_transcription", "output_transcription"),
        ("input_files", "input_files"),
        ("platform_function_processing", "platform_function_processing"),
        ("error", "error"),
        ("warning", "warning"),
    ):
        payload = data.get(legacy_key)
        if isinstance(payload, Mapping):
            return {"type": event_type, **payload}

    return None


def parse_realtime_event(data: Mapping[str, Any]) -> RealtimeServerEvent:
    event_data = _normalize_legacy_event(data)
    event_type = event_data.get("type")
    model = _EVENT_MODELS.get(event_type) if isinstance(event_type, str) else None
    if model is None:
        return RealtimeUnknownEvent.model_validate(event_data)
    return model.model_validate(event_data)


__all__ = (
    "Emotion",
    "FunctionCallEvent",
    "GigaChatModelInfo",
    "InputFileInfo",
    "InputFilesEvent",
    "InputTranscriptionEvent",
    "OutputAdditionalDataEvent",
    "OutputAudioEvent",
    "OutputInterruptedEvent",
    "OutputTranscriptionEvent",
    "PersonIdentity",
    "PlatformFunctionProcessingEvent",
    "RealtimeErrorEvent",
    "RealtimeServerEvent",
    "RealtimeServerEventType",
    "RealtimeUnknownEvent",
    "RealtimeWarningEvent",
    "parse_realtime_event",
)
