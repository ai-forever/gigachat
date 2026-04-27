from typing import Any, Dict, List, Union

from typing_extensions import Literal, NotRequired, Required, TypedDict

RealtimeMode = Literal[
    "RECOGNIZE_GIGACHAT_SYNTHESIS",
    "RECOGNIZE_SYNTHESIS",
    "GIGACHAT_SYNTHESIS",
]
RealtimeOutputModalities = Literal["AUDIO", "AUDIO_TEXT", "TEXT"]
RealtimeAudioEncoding = Literal["PCM_S16LE", "OPUS", "PCM_ALAW"]
RealtimeDurationParam = Union[float, str]


class RealtimeFirstSpeakerParam(TypedDict, total=False):
    type: Required[Literal["model", "user"]]
    lock_first_in: NotRequired[bool]


class RealtimeDisableInterruptionFunctionParam(TypedDict, total=False):
    name: Required[str]
    on_execution: NotRequired[bool]
    after_result: NotRequired[bool]


class RealtimeDisableInterruptionParam(TypedDict, total=False):
    functions: NotRequired[List[RealtimeDisableInterruptionFunctionParam]]


class RealtimeFunctionRankerParam(TypedDict, total=False):
    enable: NotRequired[bool]
    top_n: NotRequired[int]


class RealtimeFunctionRegistryParam(TypedDict, total=False):
    profile: NotRequired[str]
    labels: NotRequired[List[str]]
    ab_flags: NotRequired[str]


class RealtimeFunctionParam(TypedDict, total=False):
    name: Required[str]
    description: NotRequired[str]
    parameters: NotRequired[Dict[str, Any]]


class RealtimeGigaChatSettingsParam(TypedDict, total=False):
    model: NotRequired[str]
    preset: NotRequired[str]
    temperature: NotRequired[float]
    top_p: NotRequired[float]
    repetition_penalty: NotRequired[float]
    profanity_check: NotRequired[bool]
    filters_settings: NotRequired[Dict[str, Any]]
    function_ranker: NotRequired[RealtimeFunctionRankerParam]
    functions: NotRequired[List[RealtimeFunctionParam]]
    current_time: NotRequired[int]
    function_registry: NotRequired[RealtimeFunctionRegistryParam]
    filter_stub_phrases: NotRequired[List[str]]


class RealtimeAudioChunkMetaParam(TypedDict, total=False):
    force_co_speech: NotRequired[bool]


class RealtimeInputAudioSettingsParam(TypedDict, total=False):
    model: NotRequired[str]
    audio_encoding: NotRequired[RealtimeAudioEncoding]
    sample_rate: NotRequired[int]
    silence_phrases: NotRequired[List[str]]
    silence_phrases_timeout: NotRequired[RealtimeDurationParam]
    silence_timeout: NotRequired[RealtimeDurationParam]
    stop_phrases: NotRequired[List[str]]
    ignore_phrases: NotRequired[List[str]]


class RealtimeTriggerFunctionParam(TypedDict, total=False):
    enable: Required[bool]
    mode: NotRequired[Literal["WHITELIST", "BLACKLIST"]]
    function_names: NotRequired[List[str]]


class RealtimeTriggerGenerationParam(TypedDict, total=False):
    enable: Required[bool]
    timeout: Required[RealtimeDurationParam]


class RealtimeStubSoundsParam(TypedDict, total=False):
    trigger_function: NotRequired[RealtimeTriggerFunctionParam]
    trigger_generation: NotRequired[RealtimeTriggerGenerationParam]
    sounds: NotRequired[List[str]]


class RealtimeOutputAudioSettingsParam(TypedDict, total=False):
    voice: NotRequired[str]
    audio_encoding: NotRequired[RealtimeAudioEncoding]
    stub_sounds: NotRequired[RealtimeStubSoundsParam]


class RealtimeAudioSettingsParam(TypedDict, total=False):
    input: NotRequired[RealtimeInputAudioSettingsParam]
    output: NotRequired[RealtimeOutputAudioSettingsParam]


class RealtimeContextFunctionCallParam(TypedDict, total=False):
    name: Required[str]
    arguments: Required[Union[str, Dict[str, Any]]]


class RealtimeContextMessageParam(TypedDict, total=False):
    role: Required[str]
    content: Required[str]
    inline_data: NotRequired[Dict[str, str]]
    attachments: NotRequired[List[str]]
    function_call: NotRequired[RealtimeContextFunctionCallParam]
    function_name: NotRequired[str]
    functions_state_id: NotRequired[str]
    functions: NotRequired[List[Dict[str, Any]]]


class RealtimeContextParam(TypedDict):
    messages: List[RealtimeContextMessageParam]


class RealtimeSettingsParam(TypedDict, total=False):
    voice_call_id: Required[str]
    mode: NotRequired[RealtimeMode]
    output_modalities: NotRequired[RealtimeOutputModalities]
    first_speaker: NotRequired[RealtimeFirstSpeakerParam]
    disable_interruption: NotRequired[RealtimeDisableInterruptionParam]
    gigachat: NotRequired[RealtimeGigaChatSettingsParam]
    audio: NotRequired[RealtimeAudioSettingsParam]
    context: NotRequired[RealtimeContextParam]
    disable_vad: NotRequired[bool]
    enable_transcribe_input: NotRequired[bool]
    enable_denoiser: NotRequired[bool]
    enable_prefetch: NotRequired[bool]
    enable_person_identity: NotRequired[bool]
    enable_whisper: NotRequired[bool]
    enable_emotion: NotRequired[bool]
    enable_transcribe_silence_phrases: NotRequired[bool]
    flags: NotRequired[List[str]]


class RealtimeSettingsEventParam(TypedDict):
    type: Literal["settings"]
    settings: RealtimeSettingsParam


class RealtimeInputAudioContentEventParam(TypedDict, total=False):
    type: Required[Literal["input.audio_content"]]
    audio_chunk: Required[bytes]
    speech_start: NotRequired[bool]
    speech_end: NotRequired[bool]
    meta: NotRequired[RealtimeAudioChunkMetaParam]


class RealtimeInputSynthesisContentEventParam(TypedDict, total=False):
    type: Required[Literal["input.synthesis_content"]]
    text: Required[str]
    content_type: NotRequired[Literal["text", "ssml"]]
    is_final: NotRequired[bool]


class RealtimeFunctionResultEventParam(TypedDict, total=False):
    type: Required[Literal["function_result"]]
    content: Required[Union[str, Dict[str, Any], List[Any]]]
    function_name: NotRequired[str]


RealtimeClientEventParam = Union[
    RealtimeSettingsEventParam,
    RealtimeInputAudioContentEventParam,
    RealtimeInputSynthesisContentEventParam,
    RealtimeFunctionResultEventParam,
]

__all__ = (
    "RealtimeAudioChunkMetaParam",
    "RealtimeAudioEncoding",
    "RealtimeAudioSettingsParam",
    "RealtimeClientEventParam",
    "RealtimeContextFunctionCallParam",
    "RealtimeContextMessageParam",
    "RealtimeContextParam",
    "RealtimeDisableInterruptionFunctionParam",
    "RealtimeDisableInterruptionParam",
    "RealtimeDurationParam",
    "RealtimeFirstSpeakerParam",
    "RealtimeFunctionParam",
    "RealtimeFunctionRankerParam",
    "RealtimeFunctionRegistryParam",
    "RealtimeFunctionResultEventParam",
    "RealtimeGigaChatSettingsParam",
    "RealtimeInputAudioContentEventParam",
    "RealtimeInputAudioSettingsParam",
    "RealtimeInputSynthesisContentEventParam",
    "RealtimeMode",
    "RealtimeOutputAudioSettingsParam",
    "RealtimeOutputModalities",
    "RealtimeSettingsEventParam",
    "RealtimeSettingsParam",
    "RealtimeStubSoundsParam",
    "RealtimeTriggerFunctionParam",
    "RealtimeTriggerGenerationParam",
)
