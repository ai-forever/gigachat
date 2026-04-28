import json
import warnings
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union, cast

import pytest

from gigachat.api import realtime
from gigachat.api.realtime import AsyncRealtimeConnectionManager, RealtimeConnectionManager
from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.models.realtime import RealtimeServerEvent
from gigachat.proto.gigavoice import voice_pb2
from gigachat.resources.realtime import AsyncRealtimeResource, RealtimeResource
from gigachat.types.realtime import RealtimeSettingsParam

_PB2 = vars(voice_pb2)
_ERROR: Any = _PB2["Error"]
_GIGA_VOICE_REQUEST: Any = _PB2["GigaVoiceRequest"]
_GIGA_VOICE_RESPONSE: Any = _PB2["GigaVoiceResponse"]
_INPUT_TRANSCRIPTION: Any = _PB2["InputTranscription"]


class FakeAsyncWebSocket:
    def __init__(self, received: Optional[List[Union[str, bytes]]] = None) -> None:
        self.sent: List[Union[str, bytes]] = []
        self.received = received or []
        self.close_calls: List[Tuple[int, str]] = []

    async def send(self, data: Union[str, bytes]) -> None:
        self.sent.append(data)

    async def recv(self) -> Union[str, bytes]:
        return self.received.pop(0)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.close_calls.append((code, reason))


class FakeSyncWebSocket:
    def __init__(self, received: Optional[List[Union[str, bytes]]] = None) -> None:
        self.sent: List[Union[str, bytes]] = []
        self.received = received or []
        self.close_calls: List[Tuple[int, str]] = []

    def send(self, data: Union[str, bytes]) -> None:
        self.sent.append(data)

    def recv(self) -> Union[str, bytes]:
        return self.received.pop(0)

    def close(self, code: int = 1000, reason: str = "") -> None:
        self.close_calls.append((code, reason))


class FakeAsyncConnect:
    def __init__(self, websocket: FakeAsyncWebSocket) -> None:
        self.websocket = websocket
        self.calls: List[Dict[str, Any]] = []

    async def __call__(self, url: str, **kwargs: Any) -> FakeAsyncWebSocket:
        self.calls.append({"url": url, "kwargs": kwargs})
        return self.websocket


class FakeSyncConnect:
    def __init__(self, websocket: FakeSyncWebSocket) -> None:
        self.websocket = websocket
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, url: str, **kwargs: Any) -> FakeSyncWebSocket:
        self.calls.append({"url": url, "kwargs": kwargs})
        return self.websocket


def _settings() -> RealtimeSettingsParam:
    return {"voice_call_id": "call-id"}


def _request_from_frame(data: Union[str, bytes]) -> Any:
    assert isinstance(data, bytes)
    return _GIGA_VOICE_REQUEST.FromString(data)


def _input_transcription_frame(text: str) -> bytes:
    response = _GIGA_VOICE_RESPONSE(input_transcription=_INPUT_TRANSCRIPTION(text=text))
    return cast(bytes, response.SerializeToString())


def _error_frame(message: str) -> bytes:
    response = _GIGA_VOICE_RESPONSE(error=_ERROR(message=message))
    return cast(bytes, response.SerializeToString())


class StopDispatch(Exception):
    pass


async def test_a_realtime_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_realtime" not in client.__dict__

    resource = client.a_realtime

    assert resource is client.a_realtime
    assert isinstance(resource, AsyncRealtimeResource)


def test_realtime_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "realtime" not in client.__dict__

    resource = client.realtime

    assert resource is client.realtime
    assert isinstance(resource, RealtimeResource)


async def test_async_realtime_connect_returns_manager() -> None:
    client = GigaChatAsyncClient(realtime_url="wss://settings.test/realtime")
    headers: Mapping[str, str] = {"X-Test": "1"}
    options = {"ping_interval": 10}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        manager = client.a_realtime.connect(
            settings=_settings(),
            url="wss://argument.test/realtime",
            extra_headers=headers,
            websocket_connection_options=options,
            max_frame_size=1024,
            validate_audio_chunks=False,
        )

    assert isinstance(manager, AsyncRealtimeConnectionManager)
    assert manager._client is client
    assert manager._settings == {"voice_call_id": "call-id"}
    assert manager._url == "wss://argument.test/realtime"
    assert manager._extra_headers is headers
    assert manager._websocket_connection_options is options
    assert manager._max_frame_size == 1024
    assert manager._validate_audio_chunks is False
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_async_realtime_resource_helpers_emit_protobuf_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    websocket = FakeAsyncWebSocket([_input_transcription_frame("accepted"), _error_frame("stop")])
    connect = FakeAsyncConnect(websocket)
    monkeypatch.setattr(realtime, "_require_websockets", lambda: connect)
    client = GigaChatAsyncClient(access_token="token", realtime_url="wss://settings.test/realtime")
    event_types: List[str] = []

    manager = client.a_realtime.connect(settings=_settings(), validate_audio_chunks=False)

    @manager.on("event")
    def on_event(event: RealtimeServerEvent) -> None:
        event_types.append(event.type)
        if event.type == "error":
            raise StopDispatch

    async with manager as connection:
        await connection.input_audio.send(
            b"pcm",
            speech_start=True,
            speech_end=True,
            meta={"force_no_speech": True},
        )
        await connection.synthesis.send("hello", content_type="ssml", is_final=True)
        await connection.function_result.create({"ok": True}, function_name="tool")
        with pytest.raises(StopDispatch):
            await connection.dispatch_events()

    assert connect.calls[0]["url"] == "wss://settings.test/realtime"
    assert connect.calls[0]["kwargs"]["additional_headers"]["Authorization"] == "Bearer token"

    settings_request = _request_from_frame(websocket.sent[0])
    audio_request = _request_from_frame(websocket.sent[1])
    synthesis_request = _request_from_frame(websocket.sent[2])
    function_result_request = _request_from_frame(websocket.sent[3])

    assert settings_request.WhichOneof("request") == "settings"
    assert settings_request.settings.voice_call_id == "call-id"
    assert audio_request.input.WhichOneof("Content") == "audio_content"
    assert audio_request.input.audio_content.audio_chunk == b"pcm"
    assert audio_request.input.audio_content.meta.force_no_speech is True
    assert synthesis_request.input.WhichOneof("Content") == "content_for_synthesis"
    assert synthesis_request.input.content_for_synthesis.text == "hello"
    assert synthesis_request.input.content_for_synthesis.content_type == _PB2["ContentForSynthesis"].ContentType.Value(
        "SSML"
    )
    assert function_result_request.WhichOneof("request") == "function_result"
    assert function_result_request.function_result.function_name == "tool"
    assert json.loads(function_result_request.function_result.content) == {"ok": True}
    assert event_types == ["input_transcription", "error"]
    assert all(isinstance(frame, bytes) for frame in websocket.sent)


def test_realtime_connect_returns_manager() -> None:
    client = GigaChatSyncClient(realtime_url="wss://settings.test/realtime")
    headers: Mapping[str, str] = {"X-Test": "1"}
    options = {"ping_interval": 10}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        manager = client.realtime.connect(
            settings=_settings(),
            url="wss://argument.test/realtime",
            extra_headers=headers,
            websocket_connection_options=options,
            max_frame_size=1024,
            validate_audio_chunks=False,
        )

    assert isinstance(manager, RealtimeConnectionManager)
    assert manager._client is client
    assert manager._settings == {"voice_call_id": "call-id"}
    assert manager._url == "wss://argument.test/realtime"
    assert manager._extra_headers is headers
    assert manager._websocket_connection_options is options
    assert manager._max_frame_size == 1024
    assert manager._validate_audio_chunks is False
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_sync_realtime_resource_helpers_emit_protobuf_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    websocket = FakeSyncWebSocket([_input_transcription_frame("accepted"), _error_frame("stop")])
    connect = FakeSyncConnect(websocket)
    monkeypatch.setattr(realtime, "_require_sync_websockets", lambda: connect)
    client = GigaChatSyncClient(access_token="token", realtime_url="wss://settings.test/realtime")
    event_types: List[str] = []

    manager = client.realtime.connect(settings=_settings(), validate_audio_chunks=False)

    @manager.on("event")
    def on_event(event: RealtimeServerEvent) -> None:
        event_types.append(event.type)
        if event.type == "error":
            raise StopDispatch

    with manager as connection:
        connection.input_audio.send(
            b"pcm",
            speech_start=True,
            speech_end=True,
            meta={"force_no_speech": True},
        )
        connection.synthesis.send("hello", content_type="ssml", is_final=True)
        connection.function_result.create({"ok": True}, function_name="tool")
        with pytest.raises(StopDispatch):
            connection.dispatch_events()

    assert connect.calls[0]["url"] == "wss://settings.test/realtime"
    assert connect.calls[0]["kwargs"]["additional_headers"]["Authorization"] == "Bearer token"

    settings_request = _request_from_frame(websocket.sent[0])
    audio_request = _request_from_frame(websocket.sent[1])
    synthesis_request = _request_from_frame(websocket.sent[2])
    function_result_request = _request_from_frame(websocket.sent[3])

    assert settings_request.WhichOneof("request") == "settings"
    assert settings_request.settings.voice_call_id == "call-id"
    assert audio_request.input.WhichOneof("Content") == "audio_content"
    assert audio_request.input.audio_content.audio_chunk == b"pcm"
    assert audio_request.input.audio_content.meta.force_no_speech is True
    assert synthesis_request.input.WhichOneof("Content") == "content_for_synthesis"
    assert synthesis_request.input.content_for_synthesis.text == "hello"
    assert synthesis_request.input.content_for_synthesis.content_type == _PB2["ContentForSynthesis"].ContentType.Value(
        "SSML"
    )
    assert function_result_request.WhichOneof("request") == "function_result"
    assert function_result_request.function_result.function_name == "tool"
    assert json.loads(function_result_request.function_result.content) == {"ok": True}
    assert event_types == ["input_transcription", "error"]
    assert all(isinstance(frame, bytes) for frame in websocket.sent)
