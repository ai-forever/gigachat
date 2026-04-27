import base64
import json
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest

from gigachat.api import realtime
from gigachat.api.realtime import AsyncRealtimeConnectionManager
from gigachat.models.realtime import InputTranscriptionEvent
from gigachat.settings import Settings
from gigachat.types.realtime import RealtimeSettingsParam


class FakeWebSocket:
    def __init__(self, received: Optional[List[Union[str, bytes]]] = None) -> None:
        self.sent: List[Union[str, bytes]] = []
        self.received = received or []
        self.close_code: Optional[int] = None
        self.close_reason: Optional[str] = None
        self.close_calls: List[Tuple[int, str]] = []

    async def send(self, data: Union[str, bytes]) -> None:
        self.sent.append(data)

    async def recv(self) -> Union[str, bytes]:
        return self.received.pop(0)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.close_code = code
        self.close_reason = reason
        self.close_calls.append((code, reason))


class FakeConnect:
    def __init__(self, websocket: FakeWebSocket) -> None:
        self.websocket = websocket
        self.calls: List[Dict[str, Any]] = []

    async def __call__(self, url: str, **kwargs: Any) -> FakeWebSocket:
        self.calls.append({"url": url, "kwargs": kwargs})
        return self.websocket


class FakeClient:
    def __init__(
        self,
        *,
        realtime_url: Optional[str] = "wss://example.test/realtime",
        token: Optional[str] = "token",
        use_auth: bool = True,
        token_usable: bool = True,
    ) -> None:
        self._settings = Settings(realtime_url=realtime_url)
        self._token = token
        self._use_auth_value = use_auth
        self._token_usable = token_usable
        self.updated_token = False

    @property
    def token(self) -> Optional[str]:
        return self._token

    @property
    def _use_auth(self) -> bool:
        return self._use_auth_value

    def _is_token_usable(self) -> bool:
        return self._token_usable

    async def _aupdate_token(self) -> None:
        self.updated_token = True
        self._token = "new-token"
        self._token_usable = True


def _settings() -> RealtimeSettingsParam:
    return {"voice_call_id": "call-id"}


@pytest.mark.parametrize("url_source", ["argument", "settings"])
async def test_async_manager_connects_and_sends_initial_settings_first(url_source: str) -> None:
    websocket = FakeWebSocket()
    connect = FakeConnect(websocket)
    client = FakeClient(realtime_url="wss://settings.test/realtime")
    url = "wss://argument.test/realtime" if url_source == "argument" else None

    async with AsyncRealtimeConnectionManager(
        client,
        settings=_settings(),
        url=url,
        extra_headers={"X-Test": "1"},
        connect_factory=connect,
    ):
        pass

    assert connect.calls[0]["url"] == (url or "wss://settings.test/realtime")
    assert connect.calls[0]["kwargs"]["additional_headers"] == {
        "Authorization": "Bearer token",
        "User-Agent": "GigaChat-python-lib",
        "X-Test": "1",
    }
    assert websocket.sent[0] == '{"type":"settings","settings":{"voice_call_id":"call-id"}}'


async def test_async_manager_refreshes_token_before_connect() -> None:
    websocket = FakeWebSocket()
    connect = FakeConnect(websocket)
    client = FakeClient(token=None, token_usable=False)

    async with AsyncRealtimeConnectionManager(client, settings=_settings(), connect_factory=connect):
        pass

    assert client.updated_token is True
    assert connect.calls[0]["kwargs"]["additional_headers"]["Authorization"] == "Bearer new-token"


async def test_async_manager_queues_messages_before_connect() -> None:
    websocket = FakeWebSocket()
    connect = FakeConnect(websocket)
    manager = AsyncRealtimeConnectionManager(FakeClient(), settings=_settings(), connect_factory=connect)

    await manager.send({"type": "input.synthesis_content", "text": "hello"})
    await manager.send_raw('{"type":"raw"}')

    async with manager:
        pass

    assert websocket.sent == [
        '{"type":"settings","settings":{"voice_call_id":"call-id"}}',
        '{"type":"input.synthesis_content","text":"hello"}',
        '{"type":"raw"}',
    ]


async def test_async_connection_sends_audio_frame() -> None:
    websocket = FakeWebSocket()
    connect = FakeConnect(websocket)

    async with AsyncRealtimeConnectionManager(
        FakeClient(), settings=_settings(), connect_factory=connect
    ) as connection:
        await connection.send({"type": "input.audio_content", "audio_chunk": b"pcm", "speech_start": True})

    payload = json.loads(str(websocket.sent[1]))
    assert payload == {
        "type": "input.audio_content",
        "audio_chunk": base64.b64encode(b"pcm").decode("ascii"),
        "speech_start": True,
    }


async def test_async_connection_recv_parses_event() -> None:
    websocket = FakeWebSocket(['{"type":"input_transcription","text":"hello"}'])
    connect = FakeConnect(websocket)

    async with AsyncRealtimeConnectionManager(
        FakeClient(), settings=_settings(), connect_factory=connect
    ) as connection:
        event = await connection.recv()

    assert isinstance(event, InputTranscriptionEvent)
    assert event.text == "hello"


async def test_async_connection_parse_event_accepts_utf8_bytes() -> None:
    websocket = FakeWebSocket()
    connect = FakeConnect(websocket)

    async with AsyncRealtimeConnectionManager(
        FakeClient(), settings=_settings(), connect_factory=connect
    ) as connection:
        event = connection.parse_event(b'{"type":"input_transcription","text":"hello"}')

    assert isinstance(event, InputTranscriptionEvent)
    assert event.text == "hello"


async def test_async_connection_recv_bytes_returns_utf8_bytes() -> None:
    websocket = FakeWebSocket(['{"type":"warning","message":"slow"}'])
    connect = FakeConnect(websocket)

    async with AsyncRealtimeConnectionManager(
        FakeClient(), settings=_settings(), connect_factory=connect
    ) as connection:
        data = await connection.recv_bytes()

    assert data == b'{"type":"warning","message":"slow"}'


async def test_async_connection_close_closes_websocket() -> None:
    websocket = FakeWebSocket()
    connect = FakeConnect(websocket)

    async with AsyncRealtimeConnectionManager(
        FakeClient(), settings=_settings(), connect_factory=connect
    ) as connection:
        await connection.close(code=1001, reason="done")

    assert websocket.close_calls[0] == (1001, "done")


def test_missing_websockets_dependency_raises_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_import_module(name: str) -> Any:
        if name == "websockets.asyncio.client":
            raise ImportError("no websockets")
        raise AssertionError(name)

    monkeypatch.setattr(realtime, "import_module", fake_import_module)

    with pytest.raises(ImportError, match=r"gigachat\[realtime\]"):
        realtime._require_websockets()


async def test_async_manager_requires_realtime_url() -> None:
    manager = AsyncRealtimeConnectionManager(FakeClient(realtime_url=None), settings=_settings(), connect_factory=None)

    with pytest.raises(ValueError, match="Realtime WebSocket URL is required"):
        async with manager:
            pass
