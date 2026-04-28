from typing import TYPE_CHECKING, Any, Mapping, Optional

from gigachat.api.realtime import AsyncRealtimeConnectionManager, RealtimeConnectionManager
from gigachat.realtime._constants import MAX_CLIENT_EVENT_FRAME_SIZE
from gigachat.types.realtime import RealtimeSettingsParam

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class RealtimeResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    def connect(
        self,
        *,
        settings: RealtimeSettingsParam,
        url: Optional[str] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        websocket_connection_options: Optional[Mapping[str, Any]] = None,
        max_frame_size: int = MAX_CLIENT_EVENT_FRAME_SIZE,
        validate_audio_chunks: bool = True,
    ) -> RealtimeConnectionManager:
        """Return a realtime connection manager."""
        return RealtimeConnectionManager(
            self._base_client,
            settings=settings,
            url=url,
            extra_headers=extra_headers,
            websocket_connection_options=websocket_connection_options,
            max_frame_size=max_frame_size,
            validate_audio_chunks=validate_audio_chunks,
        )


class AsyncRealtimeResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    def connect(
        self,
        *,
        settings: RealtimeSettingsParam,
        url: Optional[str] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        websocket_connection_options: Optional[Mapping[str, Any]] = None,
        max_frame_size: int = MAX_CLIENT_EVENT_FRAME_SIZE,
        validate_audio_chunks: bool = True,
    ) -> AsyncRealtimeConnectionManager:
        """Return an async realtime connection manager."""
        return AsyncRealtimeConnectionManager(
            self._base_client,
            settings=settings,
            url=url,
            extra_headers=extra_headers,
            websocket_connection_options=websocket_connection_options,
            max_frame_size=max_frame_size,
            validate_audio_chunks=validate_audio_chunks,
        )
