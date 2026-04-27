import json
from importlib import import_module
from types import TracebackType
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Mapping, Optional, Protocol, Type, Union, cast

from gigachat.api.utils import build_headers
from gigachat.models.realtime import RealtimeServerEvent, parse_realtime_event
from gigachat.realtime._events import MAX_CLIENT_EVENT_FRAME_SIZE, serialize_client_event
from gigachat.settings import Settings
from gigachat.types.realtime import RealtimeClientEventParam, RealtimeSettingsParam


class AsyncRealtimeClientProtocol(Protocol):
    _settings: Settings

    @property
    def token(self) -> Optional[str]: ...

    @property
    def _use_auth(self) -> bool: ...

    def _is_token_usable(self) -> bool: ...

    async def _aupdate_token(self) -> None: ...


class AsyncWebSocketProtocol(Protocol):
    async def send(self, data: Union[str, bytes]) -> None: ...

    async def recv(self) -> Union[str, bytes]: ...

    async def close(self, code: int = 1000, reason: str = "") -> None: ...


AsyncWebSocketConnect = Callable[..., Awaitable[AsyncWebSocketProtocol]]
QueuedMessage = Union[RealtimeClientEventParam, str, bytes]


def _require_websockets() -> AsyncWebSocketConnect:
    try:
        module = import_module("websockets.asyncio.client")
    except ImportError as exc:
        raise ImportError("Install `gigachat[realtime]` to use realtime WebSocket API") from exc
    return cast(AsyncWebSocketConnect, cast(Any, module).connect)


class AsyncRealtimeConnectionManager:
    def __init__(
        self,
        client: AsyncRealtimeClientProtocol,
        *,
        settings: RealtimeSettingsParam,
        url: Optional[str] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        websocket_connection_options: Optional[Mapping[str, Any]] = None,
        max_frame_size: int = MAX_CLIENT_EVENT_FRAME_SIZE,
        validate_audio_chunks: bool = True,
        connect_factory: Optional[AsyncWebSocketConnect] = None,
    ) -> None:
        self._client = client
        self._settings = settings
        self._url = url
        self._extra_headers = extra_headers
        self._websocket_connection_options = websocket_connection_options
        self._max_frame_size = max_frame_size
        self._validate_audio_chunks = validate_audio_chunks
        self._connect_factory = connect_factory
        self._queued_messages: List[QueuedMessage] = []
        self._connection: Optional[AsyncRealtimeConnection] = None

    async def __aenter__(self) -> "AsyncRealtimeConnection":
        url = self._resolve_url()
        headers = await self._build_headers()
        websocket = await self._connect(url, headers)
        connection = AsyncRealtimeConnection(
            websocket,
            max_frame_size=self._max_frame_size,
            validate_audio_chunks=self._validate_audio_chunks,
        )
        self._connection = connection

        try:
            await connection.send({"type": "settings", "settings": self._settings})
            await self._flush_queued_messages(connection)
        except Exception:
            self._connection = None
            await connection.close()
            raise

        return connection

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def send(self, event: RealtimeClientEventParam) -> None:
        if self._connection is None:
            self._queued_messages.append(event)
            return
        await self._connection.send(event)

    async def send_raw(self, data: Union[str, bytes]) -> None:
        if self._connection is None:
            self._queued_messages.append(data)
            return
        await self._connection.send_raw(data)

    def _resolve_url(self) -> str:
        url = self._url or self._client._settings.realtime_url
        if not url:
            raise ValueError("Realtime WebSocket URL is required. Pass `url` or set `GIGACHAT_REALTIME_URL`.")
        return url

    async def _build_headers(self) -> Dict[str, str]:
        if self._client._use_auth and not self._client._is_token_usable():
            await self._client._aupdate_token()

        headers = build_headers(self._client.token)
        if self._extra_headers:
            headers.update(self._extra_headers)
        return headers

    async def _connect(self, url: str, headers: Mapping[str, str]) -> AsyncWebSocketProtocol:
        connect = self._connect_factory or _require_websockets()
        options = dict(self._websocket_connection_options or {})
        configured_headers = options.pop("additional_headers", None)
        if isinstance(configured_headers, Mapping):
            merged_headers = dict(configured_headers)
            merged_headers.update(headers)
            headers = merged_headers

        return await connect(url, additional_headers=dict(headers), **options)

    async def _flush_queued_messages(self, connection: "AsyncRealtimeConnection") -> None:
        queued_messages = self._queued_messages
        self._queued_messages = []
        for message in queued_messages:
            if isinstance(message, (str, bytes)):
                await connection.send_raw(message)
            else:
                await connection.send(message)


class AsyncRealtimeConnection:
    def __init__(
        self,
        websocket: AsyncWebSocketProtocol,
        *,
        max_frame_size: int = MAX_CLIENT_EVENT_FRAME_SIZE,
        validate_audio_chunks: bool = True,
    ) -> None:
        self._websocket = websocket
        self._max_frame_size = max_frame_size
        self._validate_audio_chunks = validate_audio_chunks

    async def recv(self) -> RealtimeServerEvent:
        data = await self._websocket.recv()
        return self.parse_event(data)

    async def recv_bytes(self) -> bytes:
        data = await self._websocket.recv()
        if isinstance(data, bytes):
            return data
        return data.encode("utf-8")

    async def send(self, event: RealtimeClientEventParam) -> None:
        payload = serialize_client_event(
            event,
            max_frame_size=self._max_frame_size,
            validate_audio_chunks=self._validate_audio_chunks,
        )
        await self.send_raw(payload)

    async def send_raw(self, data: Union[str, bytes]) -> None:
        if not isinstance(data, (str, bytes)):
            raise TypeError("data must be str or bytes")
        await self._websocket.send(data)

    def parse_event(self, data: Union[str, bytes]) -> RealtimeServerEvent:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        if not isinstance(data, str):
            raise TypeError("data must be str or bytes")

        json_data = json.loads(data)
        if not isinstance(json_data, Mapping):
            raise ValueError("Realtime server event must be a JSON object")
        return parse_realtime_event(json_data)

    async def close(self, *, code: int = 1000, reason: str = "") -> None:
        await self._websocket.close(code=code, reason=reason)

    def __aiter__(self) -> AsyncIterator[RealtimeServerEvent]:
        return self._iter_events()

    async def _iter_events(self) -> AsyncIterator[RealtimeServerEvent]:
        while True:
            yield await self.recv()


__all__ = (
    "AsyncRealtimeConnection",
    "AsyncRealtimeConnectionManager",
    "AsyncWebSocketConnect",
    "AsyncWebSocketProtocol",
)
